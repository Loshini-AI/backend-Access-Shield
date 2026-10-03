from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class FindingBase(BaseModel):
    severity: str
    finding_type: str
    user_id: str
    policy_id: Optional[str] = None
    service: str
    action: str
    resource: str
    risk_score: float
    confidence: float
    status: str = "Open"
    title: str
    description: str


class FindingCreate(FindingBase):
    id: str


class FindingOut(FindingBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceOut(BaseModel):
    finding_id: str
    why_flagged: str
    assigned_permission: str
    observed_usage: List[str]
    unused_actions: List[str]
    resource_scope: str
    observed_resources: List[str]
    usage_frequency: int
    last_used: Optional[str]
    risk_factors: List[str]
    confidence: float
    recommendation_reasoning: str
