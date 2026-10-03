from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.audit_report import AuditReport
from app.models.finding import Finding
from app.models.recommendation import Recommendation
from app.services.evidence_engine import EvidenceEngine
from app.services.risk_service import RiskService
from app.schemas.report import AuditReportResponse, PolicyDiffItem


class ReportService:
    """
    Service for building executive audit reports and policy diff summaries.
    """

    def __init__(self):
        self.evidence_engine = EvidenceEngine()
        self.risk_service = RiskService()

    def generate_report(self, db: Session, audit_id: str) -> AuditReportResponse:
        """
        Compiles structured audit report payload for frontend rendering or export.
        """
        report = db.query(AuditReport).filter(AuditReport.audit_id == audit_id).first()
        if not report:
            report = db.query(AuditReport).order_by(AuditReport.id.desc()).first()
            if not report:
                raise HTTPException(status_code=404, detail="No audit report found. Run an audit first.")

        findings = db.query(Finding).all()
        recommendations = db.query(Recommendation).all()

        rec_dict = {r.finding_id: r for r in recommendations}

        risk_distribution = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        for f in findings:
            risk_distribution[f.severity] = risk_distribution.get(f.severity, 0) + 1

        evidence_summaries = []
        policy_changes = []

        for f in findings:
            rec = rec_dict.get(f.id)
            rec_reason = rec.reason if rec else ""
            rec_action = rec.recommended_action if rec else f.action
            rec_resource = rec.recommended_resource if rec else f.resource

            f_raw = {
                "id": f.id,
                "action": f.action,
                "resource": f.resource,
                "finding_type": f.finding_type,
                "service": f.service,
                "observed_actions": [a.strip() for a in rec_action.split(",") if a.strip() and "NONE" not in a],
                "observed_resources": [rec_resource],
                "unused_actions": [f.action] if f.finding_type == "UNUSED_PERMISSION" else [],
                "matching_logs_count": 1 if f.finding_type != "UNUSED_PERMISSION" else 0
            }

            risk_score, confidence, severity, risk_factors = self.risk_service.calculate_risk(f_raw)

            ev = self.evidence_engine.generate_evidence(
                f_raw,
                risk_score=f.risk_score,
                confidence=f.confidence,
                risk_factors=risk_factors,
                recommendation={"reason": rec_reason}
            )
            evidence_summaries.append(ev)

            removed_acts = []
            if f.finding_type == "UNUSED_PERMISSION":
                removed_acts = [f.action]
            elif f.finding_type == "OVERBROAD_PERMISSION":
                removed_acts = [f"Unused actions under {f.action}"]

            retained_acts = f_raw["observed_actions"]

            policy_changes.append(PolicyDiffItem(
                finding_id=f.id,
                user_id=f.user_id,
                service=f.service,
                removed_actions=removed_acts,
                retained_actions=retained_acts,
                original_resource=f.resource,
                recommended_resource=rec_resource
            ))

        exec_summary = (
            f"Audit '{report.audit_id}' completed with a Least-Privilege Score of {report.least_privilege_score}/100. "
            f"Analyzed {report.policies_analyzed} policies across {report.users_analyzed} users and {report.events_analyzed} access log events. "
            f"Identified {report.findings_count} total findings including {report.high_risk_count} high/critical risk policy configurations."
        )

        return AuditReportResponse(
            report_id=report.audit_id,
            executive_summary=exec_summary,
            security_score=report.least_privilege_score,
            policies_analyzed=report.policies_analyzed,
            users_analyzed=report.users_analyzed,
            access_events=report.events_analyzed,
            findings_count=report.findings_count,
            high_risk_findings=report.high_risk_count,
            recommendations_count=len(recommendations),
            risk_distribution=risk_distribution,
            evidence_summary=evidence_summaries[:20],
            policy_changes=policy_changes
        )
