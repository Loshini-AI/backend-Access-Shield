from typing import List, Optional, Dict
from app.utils.wildcard_utils import match_wildcard

DEFAULT_DESTRUCTIVE_ACTIONS = [
    "s3:DeleteObject",
    "s3:DeleteBucket",
    "ec2:TerminateInstances",
    "rds:DeleteDBInstance",
    "iam:DeleteUser",
    "iam:DeleteRole",
    "iam:PassRole",
    "iam:AttachUserPolicy",
    "iam:PutUserPolicy",
]


def normalize_permission(effect: str, action: str, resource: str) -> Dict[str, str]:
    """
    Normalizes permission strings by trimming whitespace and standardizing format.
    """
    return {
        "effect": effect.strip().capitalize() if effect else "Allow",
        "action": action.strip(),
        "resource": resource.strip()
    }


def is_destructive_action(action: str, custom_list: Optional[List[str]] = None) -> bool:
    """
    Checks if an action is destructive based on standard or custom list.
    Handles wildcard actions (e.g. s3:*, *).
    """
    if not action:
        return False

    destructive_list = custom_list if custom_list is not None else DEFAULT_DESTRUCTIVE_ACTIONS

    action_lower = action.lower()

    if action == "*":
        return True

    for destructive in destructive_list:
        dest_lower = destructive.lower()
        if match_wildcard(action_lower, dest_lower) or match_wildcard(dest_lower, action_lower):
            return True

    return False
