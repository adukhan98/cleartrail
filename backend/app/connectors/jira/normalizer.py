"""Jira artifact normalizer."""

import hashlib
import json


def normalize_jira_issue(raw_content: dict) -> dict:
    """Normalize Jira issue to standard format."""
    fields = raw_content.get("fields", {})

    # Extract assignee
    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}

    # Extract status
    status = fields.get("status") or {}
    status_category = status.get("statusCategory", {})

    # Extract issue type
    issue_type = fields.get("issuetype") or {}

    # Extract priority
    priority = fields.get("priority") or {}

    # Extract linked issues for change management tracking
    issue_links = []
    for link in fields.get("issuelinks", []):
        linked_issue = link.get("outwardIssue") or link.get("inwardIssue")
        if linked_issue:
            issue_links.append({
                "key": linked_issue.get("key"),
                "type": link.get("type", {}).get("name"),
                "direction": "outward" if "outwardIssue" in link else "inward",
            })

    return {
        "type": "jira_issue",
        "key": raw_content.get("key"),
        "summary": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "issue_type": {
            "name": issue_type.get("name"),
            "icon_url": issue_type.get("iconUrl"),
        },
        "status": {
            "name": status.get("name"),
            "category": status_category.get("name"),  # To Do, In Progress, Done
        },
        "priority": {
            "name": priority.get("name"),
            "icon_url": priority.get("iconUrl"),
        },
        "assignee": {
            "account_id": assignee.get("accountId"),
            "display_name": assignee.get("displayName"),
            "email": assignee.get("emailAddress"),
        },
        "reporter": {
            "account_id": reporter.get("accountId"),
            "display_name": reporter.get("displayName"),
            "email": reporter.get("emailAddress"),
        },
        "labels": fields.get("labels", []),
        "components": [c.get("name") for c in fields.get("components", [])],
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "resolved": fields.get("resolutiondate"),
        "linked_issues": issue_links,
        "changelog": _extract_changelog(raw_content.get("changelog", {})),
    }


def _extract_changelog(changelog: dict) -> list[dict]:
    """Extract relevant changelog entries for audit trail."""
    entries = []
    for history in changelog.get("histories", []):
        for item in history.get("items", []):
            # Only track status changes and assignment changes
            if item.get("field") in ("status", "assignee", "resolution"):
                entries.append({
                    "field": item.get("field"),
                    "from": item.get("fromString"),
                    "to": item.get("toString"),
                    "changed_by": history.get("author", {}).get("displayName"),
                    "changed_at": history.get("created"),
                })
    return entries


def compute_content_hash(raw_content: dict) -> str:
    """Compute SHA-256 hash of issue content for integrity."""
    content_str = json.dumps(raw_content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()
