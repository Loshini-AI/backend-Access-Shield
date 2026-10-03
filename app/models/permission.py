from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(100), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    effect = Column(String(20), nullable=False, default="Allow")
    action = Column(String(255), nullable=False)
    resource = Column(String(500), nullable=False)

    policy = relationship("Policy", back_populates="permissions")
