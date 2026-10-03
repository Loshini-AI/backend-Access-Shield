import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.policy import Policy
from app.models.permission import Permission
from app.models.access_log import AccessLog
from app.models.finding import Finding
from app.models.recommendation import Recommendation
from app.models.audit_report import AuditReport
from app.services.permission_engine import PermissionEngine
from app.services.risk_service import RiskService
from app.services.recommendation_engine import RecommendationEngine
from app.services.evidence_engine import EvidenceEngine


class AuditService:
    """
    Service for executing end-to-end IAM audit workflow.
    """

    def __init__(self):
        self.permission_engine = PermissionEngine()
        self.risk_service = RiskService()
        self.recommendation_engine = RecommendationEngine()
        self.evidence_engine = EvidenceEngine()

    def run_audit(self, db: Session, audit_id: str = None) -> AuditReport:
        """
        Executes the 14-step audit workflow and persists findings and recommendations.
        """
        if not audit_id:
            audit_id = f"AUDIT-{uuid.uuid4().hex[:6].upper()}"

        started_at = datetime.now(timezone.utc)

        db_policies = db.query(Policy).all()
        db_logs = db.query(AccessLog).all()
        db_users = db.query(User).all()
        user_ids = [u.id for u in db_users]

        policies_data = []
        total_permissions_analyzed = 0
        for pol in db_policies:
            perms = []
            for p in pol.permissions:
                perms.append({
                    "effect": p.effect,
                    "action": p.action,
                    "resource": p.resource
                })
                total_permissions_analyzed += 1

            policies_data.append({
                "id": pol.id,
                "policy_name": pol.policy_name,
                "user_id": pol.user_id,
                "service": pol.service,
                "permissions": perms
            })

        logs_data = []
        for l in db_logs:
            logs_data.append({
                "user_id": l.user_id,
                "service": l.service,
                "action": l.action,
                "resource": l.resource,
                "timestamp": l.timestamp
            })

        db.query(Recommendation).filter(Recommendation.status == "Pending").delete()
        db.query(Finding).filter(Finding.status == "Open").delete()
        db.flush()

        raw_findings = []
        for u_id in user_ids:
            user_pols = [p for p in policies_data if p["user_id"] == u_id]
            if user_pols:
                u_findings = self.permission_engine.analyze_user_permissions(u_id, user_pols, logs_data)
                raw_findings.extend(u_findings)

        high_risk_count = 0
        findings_saved = 0

        for idx, f_raw in enumerate(raw_findings):
            f_id = f"FIND-{audit_id}-{idx + 1:04d}"
            f_raw["id"] = f_id

            risk_score, confidence, severity, risk_factors = self.risk_service.calculate_risk(f_raw)
            if severity in ["HIGH", "CRITICAL"]:
                high_risk_count += 1

            finding_obj = Finding(
                id=f_id,
                severity=severity,
                finding_type=f_raw["finding_type"],
                user_id=f_raw["user_id"],
                policy_id=f_raw["policy_id"],
                service=f_raw["service"],
                action=f_raw["action"],
                resource=f_raw["resource"],
                risk_score=risk_score,
                confidence=confidence,
                status="Open",
                title=f_raw["title"],
                description=f_raw["description"]
            )
            db.add(finding_obj)
            db.flush()

            rec_data = self.recommendation_engine.generate_recommendation(f_raw, risk_score)
            rec_obj = Recommendation(
                finding_id=f_id,
                current_action=rec_data["current_action"],
                recommended_action=rec_data["recommended_action"],
                current_resource=rec_data["current_resource"],
                recommended_resource=rec_data["recommended_resource"],
                reason=rec_data["reason"],
                risk_reduction=rec_data["risk_reduction"],
                confidence=rec_data["confidence"],
                status="Pending"
            )
            db.add(rec_obj)
            findings_saved += 1

        if total_permissions_analyzed == 0:
            least_privilege_score = 100.0
        else:
            penalty = min(1.0, findings_saved / max(1, total_permissions_analyzed)) * 40.0 + (high_risk_count / max(1, findings_saved)) * 60.0
            least_privilege_score = round(max(0.0, min(100.0, 100.0 - penalty)), 1)

        completed_at = datetime.now(timezone.utc)

        report_obj = db.query(AuditReport).filter(AuditReport.audit_id == audit_id).first()
        if not report_obj:
            report_obj = AuditReport(audit_id=audit_id)
            db.add(report_obj)

        report_obj.started_at = started_at
        report_obj.completed_at = completed_at
        report_obj.policies_analyzed = len(db_policies)
        report_obj.users_analyzed = len(db_users)
        report_obj.events_analyzed = len(db_logs)
        report_obj.findings_count = findings_saved
        report_obj.high_risk_count = high_risk_count
        report_obj.least_privilege_score = least_privilege_score
        report_obj.status = "completed"

        db.commit()
        db.refresh(report_obj)
        return report_obj
