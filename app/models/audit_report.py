from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(100), nullable=False, unique=True, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    policies_analyzed = Column(Integer, nullable=False, default=0)
    users_analyzed = Column(Integer, nullable=False, default=0)
    events_analyzed = Column(Integer, nullable=False, default=0)
    findings_count = Column(Integer, nullable=False, default=0)
    high_risk_count = Column(Integer, nullable=False, default=0)
    least_privilege_score = Column(Float, nullable=False, default=100.0)
    status = Column(String(50), nullable=False, default="completed")
