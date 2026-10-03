from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.audit_service import AuditService
from app.models.audit_report import AuditReport
from app.schemas.audit import AuditResponse

router = APIRouter(prefix="/audit", tags=["Audit Workflow"])


@router.post("/run", response_model=AuditResponse, summary="Run IAM Least-Privilege Audit", description="Triggers complete 14-step IAM permission vs log audit workflow.")
def run_audit(db: Session = Depends(get_db)):
    audit_service = AuditService()
    report = audit_service.run_audit(db)
    return report


@router.get("/{audit_id}", response_model=AuditResponse, summary="Get Audit Summary", description="Retrieve summary metrics for a specific audit execution.")
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    report = db.query(AuditReport).filter(AuditReport.audit_id == audit_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Audit with ID '{audit_id}' not found.")
    return report


@router.post("/reanalyze", response_model=AuditResponse, summary="Re-analyze IAM Database State", description="Re-runs audit against current database state.")
def reanalyze(db: Session = Depends(get_db)):
    audit_service = AuditService()
    report = audit_service.run_audit(db)
    return report
