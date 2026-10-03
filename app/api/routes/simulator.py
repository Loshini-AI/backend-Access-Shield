from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.access_log import AccessLog
from app.models.user import User
from app.models.finding import Finding
from app.schemas.audit import SimulatorEventRequest, SimulatorResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/simulator", tags=["Scenario Simulator"])


@router.post("/events", summary="Simulate New Access Event", description="Simulates a new access log event (e.g. Alice calls s3:DeleteObject) and saves it.")
def simulate_event(
    event: SimulatorEventRequest,
    db: Session = Depends(get_db)
):
    # Find or resolve user_id
    user = db.query(User).filter((User.id == event.user_id) | (User.name == event.user_id)).first()
    target_user_id = user.id if user else event.user_id

    log_entry = AccessLog(
        timestamp=datetime.now(timezone.utc),
        user_id=target_user_id,
        service=event.service,
        action=event.action,
        resource=event.resource,
        status=event.status,
        source_ip="192.168.1.100",
        region="us-east-1"
    )
    db.add(log_entry)
    db.commit()

    return {
        "message": f"Simulated access log event added for user '{target_user_id}'",
        "user_id": target_user_id,
        "action": event.action,
        "resource": event.resource
    }


@router.post("/reanalyze", response_model=SimulatorResponse, summary="Re-analyze Simulated Scenario", description="Re-runs audit and calculates status change for simulated events.")
def simulator_reanalyze(db: Session = Depends(get_db)):
    # Find Alice finding before re-analysis
    alice_user = db.query(User).filter((User.id == "usr-alice") | (User.name == "Alice")).first()
    alice_user_id = alice_user.id if alice_user else "usr-alice"

    previous_finding = db.query(Finding).filter(
        Finding.user_id == alice_user_id,
        Finding.action.contains("DeleteObject") | Finding.action.contains("s3:*")
    ).first()

    previous_status = "UNUSED"
    if previous_finding and "UNUSED" not in previous_finding.finding_type:
        previous_status = "USED"

    # Run audit reanalysis
    audit_service = AuditService()
    report = audit_service.run_audit(db)

    # Check finding for Alice after re-analysis
    new_finding = db.query(Finding).filter(
        Finding.user_id == alice_user_id,
        Finding.finding_type == "UNUSED_PERMISSION",
        Finding.action.contains("DeleteObject")
    ).first()

    new_status = "UNUSED" if new_finding else "USED"
    changed = (previous_status != new_status) or (new_status == "USED")

    new_risk_score = new_finding.risk_score if new_finding else 0.0

    return SimulatorResponse(
        scenario="alice-s3-demo",
        changed=changed,
        action="s3:DeleteObject",
        previous_status=previous_status,
        new_status=new_status,
        risk_score=new_risk_score,
        recommendation_updated=True,
        evidence_updated=True
    )
