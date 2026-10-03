from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AccessLogBase(BaseModel):
    user_id: str
    service: str
    action: str
    resource: str
    status: str = "SUCCESS"
    source_ip: Optional[str] = "127.0.0.1"
    region: Optional[str] = "us-east-1"
    timestamp: Optional[datetime] = None


class AccessLogCreate(AccessLogBase):
    pass


class AccessLogOut(AccessLogBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessLogUploadItem(BaseModel):
    user: Optional[str] = None
    user_id: Optional[str] = None
    service: str
    action: str
    resource: str
    status: Optional[str] = "SUCCESS"
    source_ip: Optional[str] = "127.0.0.1"
    region: Optional[str] = "us-east-1"
    timestamp: Optional[str] = None
