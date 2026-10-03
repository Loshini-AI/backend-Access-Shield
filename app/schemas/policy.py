from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PermissionBase(BaseModel):
    effect: str = "Allow"
    action: str
    resource: str


class PermissionCreate(PermissionBase):
    pass


class PermissionOut(PermissionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PolicyBase(BaseModel):
    policy_name: str
    user_id: str
    service: str
    description: Optional[str] = None


class PolicyCreate(PolicyBase):
    id: str
    permissions: List[PermissionCreate] = []


class PolicyOut(PolicyBase):
    id: str
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionOut] = []

    model_config = ConfigDict(from_attributes=True)
