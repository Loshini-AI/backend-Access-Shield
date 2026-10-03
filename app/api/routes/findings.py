from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.finding_service import FindingService
from app.schemas.finding import FindingOut

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=List[FindingOut], summary="List Audit Findings", description="Retrieves list of security findings with optional filters.")
def get_findings(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    finding_type: Optional[str] = Query(None, description="Filter by finding type"),
    service: Optional[str] = Query(None, description="Filter by AWS/Cloud service"),
    status: Optional[str] = Query(None, description="Filter by status: Open, Investigating, Accepted, Resolved"),
    user_id: Optional[str] = Query(None, description="Filter by User ID"),
    db: Session = Depends(get_db)
):
    return FindingService.get_findings(
        db,
        severity=severity,
        finding_type=finding_type,
        service=service,
        status=status,
        user_id=user_id
    )


@router.get("/{finding_id}", response_model=FindingOut, summary="Get Finding Details", description="Retrieves complete finding details for a given finding ID.")
def get_finding(finding_id: str, db: Session = Depends(get_db)):
    return FindingService.get_finding_by_id(db, finding_id)
