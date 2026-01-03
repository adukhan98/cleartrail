"""GitHub artifact normalizer."""

import hashlib
import json
from datetime import datetime

from app.connectors.base import RawArtifact


def normalize_pull_request(artifact: RawArtifact) -> dict:
    """Normalize GitHub PR to standard format.

    Extracts key fields for evidence display and control mapping.
    """
    pr = artifact.raw_content

    return {
        "type": "pull_request",
        "title": pr.get("title", ""),
        "description": pr.get("body", ""),
        "number": pr.get("number"),
        "state": pr.get("state"),  # open, closed
        "merged": pr.get("merged", False),
        "author": {
            "login": pr.get("user", {}).get("login"),
            "name": pr.get("user", {}).get("name"),
        },
        "reviewers": [
            {"login": r.get("login"), "name": r.get("name")}
            for r in pr.get("requested_reviewers", [])
        ],
        "labels": [l.get("name") for l in pr.get("labels", [])],
        "base_branch": pr.get("base", {}).get("ref"),
        "head_branch": pr.get("head", {}).get("ref"),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "merged_at": pr.get("merged_at"),
        "closed_at": pr.get("closed_at"),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changed_files": pr.get("changed_files"),
    }


def normalize_code_review(artifact: RawArtifact) -> dict:
    """Normalize GitHub code review to standard format."""
    content = artifact.raw_content
    review = content.get("review", {})

    return {
        "type": "code_review",
        "state": review.get("state"),  # APPROVED, CHANGES_REQUESTED, COMMENTED
        "reviewer": {
            "login": review.get("user", {}).get("login"),
            "name": review.get("user", {}).get("name"),
        },
        "body": review.get("body", ""),
        "pr_number": content.get("pr_number"),
        "pr_title": content.get("pr_title"),
        "submitted_at": review.get("submitted_at"),
    }


def compute_content_hash(artifact: RawArtifact) -> str:
    """Compute SHA-256 hash of artifact content for integrity."""
    content_str = json.dumps(artifact.raw_content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()


def normalize_artifact(artifact: RawArtifact) -> dict:
    """Normalize any GitHub artifact to standard format."""
    if artifact.artifact_type == "pull_request":
        return normalize_pull_request(artifact)
    elif artifact.artifact_type == "code_review":
        return normalize_code_review(artifact)
    else:
        # Return raw content for unknown types
        return artifact.raw_content
