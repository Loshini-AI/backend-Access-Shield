from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(100), primary_key=True, index=True)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    finding_type = Column(String(100), nullable=False)  # UNUSED_PERMISSION, OVERBROAD_PERMISSION, WILDCARD_ACTION, WILDCARD_RESOURCE, DESTRUCTIVE_PERMISSION, EXCESSIVE_SCOPE
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(100), ForeignKey("policies.id", ondelete="SET NULL"), nullable=True)
    service = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    resource = Column(String(500), nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=100.0)
    status = Column(String(50), nullable=False, default="Open")  # Open, Investigating, Accepted, Resolved
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    recommendations = relationship("Recommendation", back_populates="finding", cascade="all, delete-orphan")
