"""Evidence service for artifact operations."""

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import RawArtifact
from app.models.artifact import ApprovalStatus, ArtifactType, EvidenceArtifact


class EvidenceService:
    """Service for managing evidence artifacts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_artifact(
        self,
        org_id: UUID,
        raw_artifact: RawArtifact,
        normalized_content: dict,
        sync_job_id: UUID | None = None,
    ) -> EvidenceArtifact:
        """Create a new evidence artifact from raw connector data."""
        content_hash = self._compute_hash(raw_artifact.raw_content)

        artifact = EvidenceArtifact(
            org_id=org_id,
            sync_job_id=sync_job_id,
            source_system=raw_artifact.source_system,
            source_object_id=raw_artifact.source_object_id,
            source_url=raw_artifact.source_url,
            source_created_at=raw_artifact.source_created_at,
            captured_at=raw_artifact.captured_at,
            content_hash=content_hash,
            artifact_type=ArtifactType(raw_artifact.artifact_type),
            title=raw_artifact.title,
            raw_content=raw_artifact.raw_content,
            normalized_content=normalized_content,
            period_start=raw_artifact.period_start,
            period_end=raw_artifact.period_end,
            approval_status=ApprovalStatus.PENDING,
        )

        self.db.add(artifact)
        await self.db.flush()
        return artifact

    async def get_artifact(self, artifact_id: UUID, org_id: UUID) -> EvidenceArtifact | None:
        """Get artifact by ID, scoped to organization."""
        result = await self.db.execute(
            select(EvidenceArtifact).where(
                EvidenceArtifact.id == artifact_id,
                EvidenceArtifact.org_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_artifact_by_source(
        self,
        org_id: UUID,
        source_system: str,
        source_object_id: str,
    ) -> EvidenceArtifact | None:
        """Get artifact by source system and ID."""
        result = await self.db.execute(
            select(EvidenceArtifact).where(
                EvidenceArtifact.org_id == org_id,
                EvidenceArtifact.source_system == source_system,
                EvidenceArtifact.source_object_id == source_object_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_artifact(
        self,
        artifact: EvidenceArtifact,
        raw_content: dict,
        normalized_content: dict,
    ) -> EvidenceArtifact:
        """Update an existing artifact with new content."""
        artifact.raw_content = raw_content
        artifact.normalized_content = normalized_content
        artifact.content_hash = self._compute_hash(raw_content)
        artifact.captured_at = datetime.now(timezone.utc)
        await self.db.flush()
        return artifact

    async def list_artifacts(
        self,
        org_id: UUID,
        source_system: str | None = None,
        artifact_type: ArtifactType | None = None,
        approval_status: ApprovalStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EvidenceArtifact]:
        """List artifacts with optional filters."""
        query = select(EvidenceArtifact).where(EvidenceArtifact.org_id == org_id)

        if source_system:
            query = query.where(EvidenceArtifact.source_system == source_system)
        if artifact_type:
            query = query.where(EvidenceArtifact.artifact_type == artifact_type)
        if approval_status:
            query = query.where(EvidenceArtifact.approval_status == approval_status)

        query = query.order_by(EvidenceArtifact.captured_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _compute_hash(self, content: dict) -> str:
        """Compute SHA-256 hash of content for integrity verification."""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
