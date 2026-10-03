from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditResponse(BaseModel):
    audit_id: str
    status: str = "completed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    policies_analyzed: int
    users_analyzed: int
    events_analyzed: int
    findings_count: int
    high_risk_count: int
    least_privilege_score: float

    model_config = ConfigDict(from_attributes=True)


class SimulatorEventRequest(BaseModel):
    user_id: str
    service: str
    action: str
    resource: str
    status: str = "SUCCESS"


class SimulatorResponse(BaseModel):
    scenario: str
    changed: bool
    action: str
    previous_status: str
    new_status: str
    risk_score: float
    recommendation_updated: bool
    evidence_updated: bool
