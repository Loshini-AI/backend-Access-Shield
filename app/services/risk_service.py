from typing import Dict, Any, List, Tuple
from app.utils.wildcard_utils import is_wildcard_action, is_wildcard_resource
from app.utils.permission_utils import is_destructive_action


class RiskService:
    """
    Deterministic Risk Scoring Engine.
    Calculates risk score (0-100), confidence (0-100), severity, and identifies risk factors.
    """

    def calculate_risk(self, finding_data: Dict[str, Any]) -> Tuple[float, float, str, List[str]]:
        """
        Calculates (risk_score, confidence, severity, risk_factors) for a given finding raw data.
        """
        finding_type = finding_data.get("finding_type", "")
        action = finding_data.get("action", "")
        resource = finding_data.get("resource", "")
        matching_logs_count = finding_data.get("matching_logs_count", 0)
        observed_actions = finding_data.get("observed_actions", [])

        score = 0.0
        confidence = 90.0
        risk_factors = []

        is_wild_act = is_wildcard_action(action)
        is_wild_res = is_wildcard_resource(resource)
        is_dest = is_destructive_action(action)

        if is_wild_act:
            score += 25.0
            risk_factors.append("Wildcard action assigned")

        if is_wild_res:
            score += 20.0
            risk_factors.append("Wildcard resource scope assigned")

        if is_dest:
            if is_wild_act or is_wild_res:
                score += 30.0
                risk_factors.append("Unrestricted destructive action granted")
            elif matching_logs_count == 0:
                score += 25.0
                risk_factors.append("Unused destructive permission")
            else:
                score += 15.0
                risk_factors.append("Active destructive action granted")

        if finding_type == "UNUSED_PERMISSION":
            score += 20.0
            risk_factors.append("Granted permission never used in access logs")
        elif finding_type == "OVERBROAD_PERMISSION":
            score += 25.0
            risk_factors.append("Granted scope significantly exceeds observed usage")
        elif finding_type == "EXCESSIVE_SCOPE":
            score += 15.0
            risk_factors.append("Resource scope broader than accessed target resources")

        if matching_logs_count == 0:
            confidence = 95.0
            risk_factors.append("Zero log access events recorded")
        else:
            confidence = min(100.0, 80.0 + min(len(observed_actions) * 5, 20.0))

        risk_score = round(max(0.0, min(100.0, score)), 1)
        confidence = round(max(0.0, min(100.0, confidence)), 1)

        if risk_score >= 80.0:
            severity = "CRITICAL"
        elif risk_score >= 60.0:
            severity = "HIGH"
        elif risk_score >= 35.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return risk_score, confidence, severity, risk_factors
