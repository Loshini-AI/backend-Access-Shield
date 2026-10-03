from typing import List, Dict, Any
from pydantic import BaseModel


class PolicyDiffItem(BaseModel):
    finding_id: str
    user_id: str
    service: str
    removed_actions: List[str]
    retained_actions: List[str]
    original_resource: str
    recommended_resource: str


class AuditReportResponse(BaseModel):
    report_id: str
    executive_summary: str
    security_score: float
    policies_analyzed: int
    users_analyzed: int
    access_events: int
    findings_count: int
    high_risk_findings: int
    recommendations_count: int
    risk_distribution: Dict[str, int]
    evidence_summary: List[Dict[str, Any]]
    policy_changes: List[PolicyDiffItem]
