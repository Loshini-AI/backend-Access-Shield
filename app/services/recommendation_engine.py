from typing import Dict, Any, List
from app.utils.wildcard_utils import is_wildcard_action, is_wildcard_resource


class RecommendationEngine:
    """
    Recommendation Engine for generating least-privilege policy fixes.
    """

    def generate_recommendation(
        self,
        finding_data: Dict[str, Any],
        risk_score: float
    ) -> Dict[str, Any]:
        """
        Produces least-privilege recommendation for a given finding.
        """
        action = finding_data.get("action", "")
        resource = finding_data.get("resource", "")
        finding_type = finding_data.get("finding_type", "")
        service = finding_data.get("service", "")
        observed_actions = finding_data.get("observed_actions", [])
        observed_resources = finding_data.get("observed_resources", [])
        unused_actions = finding_data.get("unused_actions", [])

        recommended_action = action
        recommended_resource = resource
        reason_parts = []

        if is_wildcard_action(action):
            if observed_actions:
                recommended_action = ", ".join(sorted(observed_actions))
                reason_parts.append(
                    f"Replace wildcard '{action}' with explicitly observed action(s): {recommended_action}."
                )
            else:
                recommended_action = "NONE (Remove Action)"
                reason_parts.append(
                    f"No actions under wildcard '{action}' were ever observed. Recommend removing this action block."
                )
        elif finding_type == "UNUSED_PERMISSION":
            if unused_actions and action in unused_actions:
                recommended_action = "NONE (Remove Action)"
                reason_parts.append(
                    f"Action '{action}' was never observed in access logs. Recommend removing it from policy."
                )
            elif observed_actions:
                recommended_action = ", ".join(sorted(observed_actions))
                reason_parts.append(
                    f"Retain only observed action(s): {recommended_action}."
                )
            else:
                recommended_action = "NONE (Remove Action)"
                reason_parts.append(
                    f"Action '{action}' is completely unused in observed logs. Recommend removing."
                )

        if is_wildcard_resource(resource):
            if observed_resources:
                if len(observed_resources) == 1:
                    recommended_resource = observed_resources[0]
                else:
                    common_prefix = self._find_common_arn_prefix(observed_resources)
                    recommended_resource = common_prefix if common_prefix else ", ".join(sorted(observed_resources))
                reason_parts.append(
                    f"Narrow wildcard resource scope '{resource}' to observed target resource(s): {recommended_resource}."
                )
            else:
                reason_parts.append(
                    f"No specific resource accesses recorded for '{resource}'."
                )

        if not reason_parts:
            reason = f"The policy permission '{action}' on '{resource}' was reviewed. Recommend applying least privilege."
        else:
            reason = (
                f"The assigned policy grants broader {service.upper()} access than the observed access pattern requires. "
                + " ".join(reason_parts)
            )

        risk_reduction = round(min(100.0, max(20.0, risk_score * 0.85)), 1)
        confidence = 95.0

        return {
            "current_action": action,
            "recommended_action": recommended_action,
            "current_resource": resource,
            "recommended_resource": recommended_resource,
            "reason": reason,
            "risk_reduction": risk_reduction,
            "confidence": confidence,
            "status": "Pending"
        }

    def _find_common_arn_prefix(self, arns: List[str]) -> str:
        """
        Derives a common IAM resource ARN pattern if possible.
        """
        if not arns:
            return "*"
        if len(arns) == 1:
            return arns[0]

        first = arns[0]
        if "/" in first:
            base_prefix = first.rsplit("/", 1)[0] + "/*"
            if all(arn.startswith(first.rsplit("/", 1)[0]) for arn in arns):
                return base_prefix

        return ", ".join(sorted(arns))
