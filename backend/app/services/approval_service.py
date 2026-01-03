"""Approval workflow service."""

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ApprovalRecord, ApprovalStatus, EvidenceArtifact
from app.models.audit_log import AuditEventType, AuditLog
from app.models.user import User


class ApprovalService:
    """Service for managing artifact approvals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def approve_artifact(
        self,
        artifact: EvidenceArtifact,
        user: User,
        notes: str | None = None,
    ) -> ApprovalRecord:
        """Record approval for an artifact."""
        approved_at = datetime.now(timezone.utc)

        # Create signature hash for integrity
        signature_data = f"{artifact.id}:{user.id}:{approved_at.isoformat()}:approved"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        approval = ApprovalRecord(
            artifact_id=artifact.id,
            user_id=user.id,
            approved=True,
            approved_at=approved_at,
            notes=notes,
            signature_hash=signature_hash,
        )
        self.db.add(approval)

        # Update artifact status
        artifact.approval_status = ApprovalStatus.APPROVED

        # Create audit log entry
        audit_log = AuditLog(
            org_id=artifact.org_id,
            user_id=user.id,
            event_type=AuditEventType.ARTIFACT_APPROVED,
            entity_type="evidence_artifact",
            entity_id=artifact.id,
            new_value={"approved": True, "notes": notes},
            description=f"Artifact '{artifact.title}' approved by {user.name}",
        )
        self.db.add(audit_log)

        await self.db.flush()
        return approval

    async def reject_artifact(
        self,
        artifact: EvidenceArtifact,
        user: User,
        notes: str,
    ) -> ApprovalRecord:
        """Record rejection for an artifact."""
        rejected_at = datetime.now(timezone.utc)

        signature_data = f"{artifact.id}:{user.id}:{rejected_at.isoformat()}:rejected"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        rejection = ApprovalRecord(
            artifact_id=artifact.id,
            user_id=user.id,
            approved=False,
            approved_at=rejected_at,
            notes=notes,
            signature_hash=signature_hash,
        )
        self.db.add(rejection)

        # Update artifact status
        artifact.approval_status = ApprovalStatus.REJECTED

        # Create audit log entry
        audit_log = AuditLog(
            org_id=artifact.org_id,
            user_id=user.id,
            event_type=AuditEventType.ARTIFACT_REJECTED,
            entity_type="evidence_artifact",
            entity_id=artifact.id,
            new_value={"approved": False, "notes": notes},
            description=f"Artifact '{artifact.title}' rejected by {user.name}: {notes}",
        )
        self.db.add(audit_log)

        await self.db.flush()
        return rejection

    async def get_approval_history(
        self,
        artifact_id: UUID,
    ) -> list[ApprovalRecord]:
        """Get approval history for an artifact."""
        result = await self.db.execute(
            select(ApprovalRecord)
            .where(ApprovalRecord.artifact_id == artifact_id)
            .order_by(ApprovalRecord.approved_at.desc())
        )
        return list(result.scalars().all())

    async def verify_signature(self, approval: ApprovalRecord) -> bool:
        """Verify approval record integrity."""
        status = "approved" if approval.approved else "rejected"
        expected_data = (
            f"{approval.artifact_id}:{approval.user_id}:"
            f"{approval.approved_at.isoformat()}:{status}"
        )
        expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
        return approval.signature_hash == expected_hash
