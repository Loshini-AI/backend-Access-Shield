from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.report_service import ReportService
from app.schemas.report import AuditReportResponse

router = APIRouter(prefix="/reports", tags=["Audit Reports"])


@router.get("/{report_id}", response_model=AuditReportResponse, summary="Get Executive Audit Report", description="Returns structured report data for executive dashboard rendering.")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report_service = ReportService()
    return report_service.generate_report(db, report_id)
