from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = Column(String(100), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    resource = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="SUCCESS")
    source_ip = Column(String(50), nullable=True)
    region = Column(String(50), nullable=True)

    user = relationship("User", back_populates="access_logs")
