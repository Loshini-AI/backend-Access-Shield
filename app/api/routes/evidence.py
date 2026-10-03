from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.finding_service import FindingService
from app.services.evidence_engine import EvidenceEngine
from app.services.risk_service import RiskService
from app.models.recommendation import Recommendation
from app.schemas.finding import EvidenceOut

router = APIRouter(prefix="/findings", tags=["Evidence"])


@router.get("/{finding_id}/evidence", response_model=EvidenceOut, summary="Get Finding Evidence", description="Returns explainable evidence for a given finding.")
def get_finding_evidence(finding_id: str, db: Session = Depends(get_db)):
    finding = FindingService.get_finding_by_id(db, finding_id)
    rec = db.query(Recommendation).filter(Recommendation.finding_id == finding_id).first()

    rec_reason = rec.reason if rec else ""
    rec_action = rec.recommended_action if rec else finding.action
    rec_resource = rec.recommended_resource if rec else finding.resource

    f_raw = {
        "id": finding.id,
        "action": finding.action,
        "resource": finding.resource,
        "finding_type": finding.finding_type,
        "service": finding.service,
        "observed_actions": [a.strip() for a in rec_action.split(",") if a.strip() and "NONE" not in a],
        "observed_resources": [rec_resource],
        "unused_actions": [finding.action] if finding.finding_type == "UNUSED_PERMISSION" else [],
        "matching_logs_count": 1 if finding.finding_type != "UNUSED_PERMISSION" else 0
    }

    risk_service = RiskService()
    evidence_engine = EvidenceEngine()

    risk_score, confidence, severity, risk_factors = risk_service.calculate_risk(f_raw)

    return evidence_engine.generate_evidence(
        f_raw,
        risk_score=finding.risk_score,
        confidence=finding.confidence,
        risk_factors=risk_factors,
        recommendation={"reason": rec_reason}
    )
