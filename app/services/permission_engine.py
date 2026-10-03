from typing import List, Dict, Any, Set
from app.utils.wildcard_utils import match_wildcard, is_wildcard_action, is_wildcard_resource
from app.utils.permission_utils import is_destructive_action

KNOWN_SERVICE_ACTIONS = {
    "s3": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket", "s3:GetBucketLocation"],
    "ec2": ["ec2:StartInstances", "ec2:StopInstances", "ec2:TerminateInstances", "ec2:DescribeInstances", "ec2:RunInstances"],
    "lambda": ["lambda:InvokeFunction", "lambda:CreateFunction", "lambda:DeleteFunction", "lambda:ListFunctions"],
    "rds": ["rds:DescribeDBInstances", "rds:CreateDBInstance", "rds:DeleteDBInstance", "rds:RebootDBInstance"],
    "iam": ["iam:GetUser", "iam:CreateUser", "iam:DeleteUser", "iam:ListUsers", "iam:PassRole", "iam:DeleteRole"]
}


class PermissionEngine:
    """
    Engine for comparing Granted Permissions vs Observed Access Logs.
    Detects UNUSED_PERMISSION, OVERBROAD_PERMISSION, WILDCARD_ACTION,
    WILDCARD_RESOURCE, DESTRUCTIVE_PERMISSION, EXCESSIVE_SCOPE.
    """

    def __init__(self):
        pass

    def analyze_user_permissions(
        self,
        user_id: str,
        policies: List[Dict[str, Any]],
        access_logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compares granted permissions in policies with observed access logs for a specific user.
        Returns a list of raw finding specifications.
        """
        findings = []

        # Filter logs for user
        user_logs = [log for log in access_logs if log.get("user_id") == user_id]

        for policy in policies:
            policy_id = policy.get("id")
            service = policy.get("service", "unknown")
            permissions = policy.get("permissions", [])

            for perm in permissions:
                effect = perm.get("effect", "Allow")
                if effect != "Allow":
                    continue

                action = perm.get("action", "")
                resource = perm.get("resource", "")

                matching_logs = [
                    log for log in user_logs
                    if match_wildcard(log.get("service", ""), service) or
                       match_wildcard(action, log.get("action", ""))
                ]

                observed_actions = list(set([log["action"] for log in matching_logs if "action" in log]))
                observed_resources = list(set([log["resource"] for log in matching_logs if "resource" in log]))

                is_wild_act = is_wildcard_action(action)
                is_wild_res = is_wildcard_resource(resource)
                is_dest = is_destructive_action(action)

                # 1. Wildcard Action Detection
                if is_wild_act:
                    findings.append({
                        "finding_type": "WILDCARD_ACTION",
                        "user_id": user_id,
                        "policy_id": policy_id,
                        "service": service,
                        "action": action,
                        "resource": resource,
                        "title": f"Wildcard Action Granted: {action}",
                        "description": f"Policy '{policy.get('policy_name')}' grants wildcard action '{action}' on service '{service}'.",
                        "observed_actions": observed_actions,
                        "observed_resources": observed_resources,
                        "matching_logs_count": len(matching_logs),
                    })

                # 2. Wildcard Resource Detection
                if is_wild_res:
                    findings.append({
                        "finding_type": "WILDCARD_RESOURCE",
                        "user_id": user_id,
                        "policy_id": policy_id,
                        "service": service,
                        "action": action,
                        "resource": resource,
                        "title": f"Wildcard Resource Scope: {resource}",
                        "description": f"Permission grants access to all resources ('*') for action '{action}'.",
                        "observed_actions": observed_actions,
                        "observed_resources": observed_resources,
                        "matching_logs_count": len(matching_logs),
                    })

                # 3. Destructive Permission Detection
                if is_dest:
                    destructive_used = any(
                        is_destructive_action(log_act) for log_act in observed_actions
                    )
                    findings.append({
                        "finding_type": "DESTRUCTIVE_PERMISSION",
                        "user_id": user_id,
                        "policy_id": policy_id,
                        "service": service,
                        "action": action,
                        "resource": resource,
                        "title": f"Destructive Permission Granted: {action}",
                        "description": f"Policy grants potentially destructive action '{action}'. Observed usage: {len(observed_actions)} action(s).",
                        "observed_actions": observed_actions,
                        "observed_resources": observed_resources,
                        "matching_logs_count": len(matching_logs),
                        "destructive_used": destructive_used
                    })

                # 4. Unused & Overbroad Permission Analysis
                if is_wild_act:
                    findings.append({
                        "finding_type": "OVERBROAD_PERMISSION",
                        "user_id": user_id,
                        "policy_id": policy_id,
                        "service": service,
                        "action": action,
                        "resource": resource,
                        "title": f"Overbroad Permission: {action}",
                        "description": f"Wildcard permission '{action}' is assigned, but only {len(observed_actions)} specific action(s) were observed in logs.",
                        "observed_actions": observed_actions,
                        "observed_resources": observed_resources,
                        "matching_logs_count": len(matching_logs),
                    })

                    svc_key = service.lower()
                    known_acts = KNOWN_SERVICE_ACTIONS.get(svc_key, [])
                    unused_acts = [
                        act for act in known_acts
                        if match_wildcard(action, act) and act not in observed_actions
                    ]
                    if unused_acts:
                        findings.append({
                            "finding_type": "UNUSED_PERMISSION",
                            "user_id": user_id,
                            "policy_id": policy_id,
                            "service": service,
                            "action": action,
                            "resource": resource,
                            "title": f"Unused Permission Actions in {action}",
                            "description": f"Actions {unused_acts} granted via '{action}' were never observed in access logs.",
                            "observed_actions": observed_actions,
                            "observed_resources": observed_resources,
                            "matching_logs_count": len(matching_logs),
                            "unused_actions": unused_acts
                        })
                else:
                    if not observed_actions or action not in observed_actions:
                        findings.append({
                            "finding_type": "UNUSED_PERMISSION",
                            "user_id": user_id,
                            "policy_id": policy_id,
                            "service": service,
                            "action": action,
                            "resource": resource,
                            "title": f"Unused Permission: {action}",
                            "description": f"Permission '{action}' was granted but never observed in access logs.",
                            "observed_actions": [],
                            "observed_resources": observed_resources,
                            "matching_logs_count": 0,
                            "unused_actions": [action]
                        })

                # 5. Excessive Scope Detection
                if is_wild_res and observed_resources:
                    findings.append({
                        "finding_type": "EXCESSIVE_SCOPE",
                        "user_id": user_id,
                        "policy_id": policy_id,
                        "service": service,
                        "action": action,
                        "resource": resource,
                        "title": f"Excessive Resource Scope for {action}",
                        "description": f"Resource is scoped to wildcard '{resource}', but user only accessed {len(observed_resources)} specific resource(s).",
                        "observed_actions": observed_actions,
                        "observed_resources": observed_resources,
                        "matching_logs_count": len(matching_logs),
                    })

        return findings
