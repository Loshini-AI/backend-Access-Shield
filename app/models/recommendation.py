from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(100), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    current_action = Column(String(255), nullable=False)
    recommended_action = Column(String(255), nullable=False)
    current_resource = Column(String(500), nullable=False)
    recommended_resource = Column(String(500), nullable=False)
    reason = Column(String(1000), nullable=False)
    risk_reduction = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=100.0)
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Accepted, Rejected, Reviewed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    finding = relationship("Finding", back_populates="recommendations")
