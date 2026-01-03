"""Evidence sync tasks."""

import asyncio
from datetime import date, datetime, timezone
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.connectors.base import DateRange
from app.connectors.registry import connector_registry
from app.connectors.github.normalizer import normalize_artifact as normalize_github
from app.connectors.jira.normalizer import normalize_jira_issue
from app.models.integration import Integration, SyncJob, SyncJobStatus
from app.models.audit_log import AuditEventType, AuditLog
from app.services.evidence_service import EvidenceService
from app.services.mapping_service import MappingService


@shared_task(bind=True, max_retries=3)
def sync_integration(self, integration_id: str, date_range_start: str, date_range_end: str) -> dict:
    """Sync evidence from an integration.

    Args:
        integration_id: UUID of the integration to sync
        date_range_start: Start date in ISO format
        date_range_end: End date in ISO format

    Returns:
        Dict with sync results
    """
    return asyncio.run(
        _sync_integration_async(
            UUID(integration_id),
            date.fromisoformat(date_range_start),
            date.fromisoformat(date_range_end),
        )
    )


async def _sync_integration_async(
    integration_id: UUID,
    start_date: date,
    end_date: date,
) -> dict:
    """Async implementation of integration sync."""
    async with async_session_maker() as db:
        # Get integration
        integration = await db.get(Integration, integration_id)
        if not integration:
            return {"error": "Integration not found"}

        # Create sync job
        sync_job = SyncJob(
            integration_id=integration_id,
            status=SyncJobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        db.add(sync_job)
        await db.flush()

        # Log sync start
        audit_log = AuditLog(
            org_id=integration.org_id,
            event_type=AuditEventType.INTEGRATION_SYNC_STARTED,
            entity_type="integration",
            entity_id=integration_id,
            description=f"Started sync for {integration.connector_type.value}",
        )
        db.add(audit_log)

        try:
            # Get connector
            connector = connector_registry.get(integration.connector_type.value)
            if not connector:
                raise ValueError(f"Unknown connector type: {integration.connector_type}")

            # Decrypt and set credentials
            # TODO: Implement credential decryption
            # connector.set_credentials(decrypt_credentials(integration.encrypted_credentials))

            # Initialize services
            evidence_service = EvidenceService(db)
            mapping_service = MappingService(db)

            date_range = DateRange(start=start_date, end=end_date)
            artifacts_found = 0
            artifacts_created = 0

            # Get resources to sync from config
            resource_ids = integration.config.get("resource_ids", []) if integration.config else []

            for resource_id in resource_ids:
                async for raw_artifact in connector.fetch_artifacts(resource_id, date_range):
                    artifacts_found += 1

                    # Check if artifact already exists
                    existing = await evidence_service.get_artifact_by_source(
                        integration.org_id,
                        raw_artifact.source_system,
                        raw_artifact.source_object_id,
                    )

                    # Normalize based on source system
                    if raw_artifact.source_system == "github":
                        normalized = normalize_github(raw_artifact)
                    elif raw_artifact.source_system == "jira":
                        normalized = normalize_jira_issue(raw_artifact.raw_content)
                    else:
                        normalized = raw_artifact.raw_content

                    if existing:
                        # Update existing artifact
                        await evidence_service.update_artifact(
                            existing,
                            raw_artifact.raw_content,
                            normalized,
                        )
                    else:
                        # Create new artifact
                        artifact = await evidence_service.create_artifact(
                            integration.org_id,
                            raw_artifact,
                            normalized,
                            sync_job.id,
                        )
                        artifacts_created += 1

                        # Auto-map to controls
                        await mapping_service.auto_map_artifact(artifact)

            # Update sync job
            sync_job.status = SyncJobStatus.COMPLETED
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.artifacts_found = artifacts_found
            sync_job.artifacts_created = artifacts_created

            # Update integration
            integration.last_sync_at = datetime.now(timezone.utc)

            # Log completion
            audit_log = AuditLog(
                org_id=integration.org_id,
                event_type=AuditEventType.INTEGRATION_SYNC_COMPLETED,
                entity_type="integration",
                entity_id=integration_id,
                new_value={
                    "artifacts_found": artifacts_found,
                    "artifacts_created": artifacts_created,
                },
                description=f"Completed sync: {artifacts_created} new artifacts",
            )
            db.add(audit_log)

            await db.commit()

            return {
                "status": "completed",
                "artifacts_found": artifacts_found,
                "artifacts_created": artifacts_created,
            }

        except Exception as e:
            # Update sync job with failure
            sync_job.status = SyncJobStatus.FAILED
            sync_job.completed_at = datetime.now(timezone.utc)
            sync_job.error_details = {"error": str(e)}

            # Log failure
            audit_log = AuditLog(
                org_id=integration.org_id,
                event_type=AuditEventType.INTEGRATION_SYNC_FAILED,
                entity_type="integration",
                entity_id=integration_id,
                new_value={"error": str(e)},
                description=f"Sync failed: {str(e)}",
            )
            db.add(audit_log)

            await db.commit()

            return {"status": "failed", "error": str(e)}
