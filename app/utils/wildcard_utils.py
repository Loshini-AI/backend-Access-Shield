import fnmatch
import re


def match_wildcard(pattern: str, target: str) -> bool:
    """
    Matches IAM wildcard patterns.
    Examples:
        match_wildcard("s3:*", "s3:GetObject") -> True
        match_wildcard("*", "ec2:StartInstances") -> True
        match_wildcard("arn:aws:s3:::prod/*", "arn:aws:s3:::prod/file.txt") -> True
    """
    if not pattern or not target:
        return False

    if pattern == "*":
        return True

    # Normalize case for comparison if service/action prefix
    pattern_lower = pattern.lower()
    target_lower = target.lower()

    return fnmatch.fnmatch(target_lower, pattern_lower)


def is_wildcard_action(action: str) -> bool:
    """
    Checks if action contains a wildcard.
    """
    if not action:
        return False
    return "*" in action or "?" in action


def is_wildcard_resource(resource: str) -> bool:
    """
    Checks if resource contains a wildcard.
    """
    if not resource:
        return False
    return "*" in resource or "?" in resource
