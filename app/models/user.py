from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="Active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    policies = relationship("Policy", back_populates="user", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="user", cascade="all, delete-orphan")
