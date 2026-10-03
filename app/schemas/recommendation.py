from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RecommendationBase(BaseModel):
    finding_id: str
    current_action: str
    recommended_action: str
    current_resource: str
    recommended_resource: str
    reason: str
    risk_reduction: float
    confidence: float
    status: str = "Pending"


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationOut(RecommendationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
