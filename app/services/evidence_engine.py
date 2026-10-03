from typing import Dict, Any, List


class EvidenceEngine:
    """
    Evidence Engine for generating detailed, explainable security evidence summaries.
    """

    def generate_evidence(
        self,
        finding_data: Dict[str, Any],
        risk_score: float,
        confidence: float,
        risk_factors: List[str],
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Produces complete explainable evidence payload for a finding.
        """
        finding_id = finding_data.get("id", "finding-unknown")
        action = finding_data.get("action", "")
        resource = finding_data.get("resource", "")
        finding_type = finding_data.get("finding_type", "")
        service = finding_data.get("service", "")
        observed_actions = finding_data.get("observed_actions", [])
        observed_resources = finding_data.get("observed_resources", [])
        unused_actions = finding_data.get("unused_actions", [])
        if not unused_actions and "*" in action:
            try:
                from app.services.permission_engine import KNOWN_SERVICE_ACTIONS, match_wildcard
                unused_actions = [
                    a for a in KNOWN_SERVICE_ACTIONS.get(service.lower(), [])
                    if match_wildcard(action, a) and a not in observed_actions
                ]
            except ImportError:
                pass
        matching_logs_count = finding_data.get("matching_logs_count", 0)

        if finding_type == "UNUSED_PERMISSION":
            why_flagged = f"The user has '{action}' granted for service '{service}', but no access matching this action was observed."
        elif finding_type == "OVERBROAD_PERMISSION":
            why_flagged = f"The user has broad permission '{action}', but only {len(observed_actions)} action(s) ({', '.join(observed_actions)}) were observed in access logs."
        elif finding_type == "WILDCARD_ACTION":
            why_flagged = f"The policy grants full wildcard action access '{action}' to service '{service}'."
        elif finding_type == "WILDCARD_RESOURCE":
            why_flagged = f"The policy grants wildcard resource access ('*') allowing actions on all resources in '{service}'."
        elif finding_type == "DESTRUCTIVE_PERMISSION":
            why_flagged = f"The user has destructive action '{action}' assigned. Usage frequency is {matching_logs_count} event(s)."
        elif finding_type == "EXCESSIVE_SCOPE":
            why_flagged = f"Resource scope is set to wildcard '{resource}', but access logs only show interaction with specific targets."
        else:
            why_flagged = f"Permission '{action}' on '{resource}' violates least-privilege principles."

        return {
            "finding_id": finding_id,
            "why_flagged": why_flagged,
            "assigned_permission": f"Effect: Allow | Action: {action} | Resource: {resource}",
            "observed_usage": observed_actions,
            "unused_actions": unused_actions,
            "resource_scope": resource,
            "observed_resources": observed_resources,
            "usage_frequency": matching_logs_count,
            "last_used": "Within 90-day log window" if matching_logs_count > 0 else "Never",
            "risk_factors": risk_factors,
            "confidence": confidence,
            "recommendation_reasoning": recommendation.get("reason", "")
        }
