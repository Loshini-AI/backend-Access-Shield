from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.finding import Finding
from app.models.recommendation import Recommendation


class FindingService:
    """
    Database service for findings, recommendations, and evidence retrieval.
    """

    @staticmethod
    def get_findings(
        db: Session,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None,
        service: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Finding]:
        query = db.query(Finding)

        if severity:
            query = query.filter(Finding.severity == severity)
        if finding_type:
            query = query.filter(Finding.finding_type == finding_type)
        if service:
            query = query.filter(Finding.service == service)
        if status:
            query = query.filter(Finding.status == status)
        if user_id:
            query = query.filter(Finding.user_id == user_id)

        return query.all()

    @staticmethod
    def get_finding_by_id(db: Session, finding_id: str) -> Finding:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail=f"Finding with ID '{finding_id}' not found.")
        return finding

    @staticmethod
    def get_recommendations(db: Session, status: Optional[str] = None) -> List[Recommendation]:
        query = db.query(Recommendation)
        if status:
            query = query.filter(Recommendation.status == status)
        return query.all()

    @staticmethod
    def update_recommendation_status(
        db: Session,
        rec_id: int,
        new_status: str
    ) -> Recommendation:
        rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation with ID '{rec_id}' not found.")

        rec.status = new_status

        finding = db.query(Finding).filter(Finding.id == rec.finding_id).first()
        if finding:
            if new_status == "Accepted":
                finding.status = "Resolved"
            elif new_status == "Rejected":
                finding.status = "Open"

        db.commit()
        db.refresh(rec)
        return rec
