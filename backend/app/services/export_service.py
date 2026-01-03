"""Export service for generating audit-ready packages."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ApprovalStatus
from app.models.packet import EvidencePacket, PacketStatus


class ExportService:
    """Service for exporting evidence packets."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_manifest(
        self,
        packet: EvidencePacket,
        generated_by: str,
    ) -> dict[str, Any]:
        """Generate evidence manifest for auditor.

        The manifest provides a complete inventory of all evidence
        with provenance information for auditor verification.
        """
        manifest = {
            "manifest_version": "1.0",
            "packet_id": str(packet.id),
            "control_id": packet.control_id,
            "title": packet.title,
            "audit_period": {
                "start": packet.period_start.isoformat(),
                "end": packet.period_end.isoformat(),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": generated_by,
            "narrative": {
                "content": packet.ai_narrative,
                "generated_at": (
                    packet.narrative_generated_at.isoformat()
                    if packet.narrative_generated_at
                    else None
                ),
                "approved_by": str(packet.narrative_approved_by) if packet.narrative_approved_by else None,
                "approved_at": (
                    packet.narrative_approved_at.isoformat()
                    if packet.narrative_approved_at
                    else None
                ),
            },
            "evidence_items": [],
            "summary": {
                "total_items": 0,
                "approved_items": 0,
                "pending_items": 0,
                "by_source": {},
                "by_type": {},
            },
        }

        # Build evidence items list
        for item in packet.items:
            artifact = item.artifact

            # Get latest approval
            latest_approval = None
            if artifact.approvals:
                latest_approval = max(artifact.approvals, key=lambda a: a.approved_at)

            evidence_item = {
                "artifact_id": str(artifact.id),
                "display_order": item.display_order,
                "title": artifact.title,
                "artifact_type": artifact.artifact_type.value,
                "source": {
                    "system": artifact.source_system,
                    "object_id": artifact.source_object_id,
                    "url": artifact.source_url,
                    "created_at": (
                        artifact.source_created_at.isoformat()
                        if artifact.source_created_at
                        else None
                    ),
                },
                "provenance": {
                    "captured_at": artifact.captured_at.isoformat(),
                    "content_hash": artifact.content_hash,
                },
                "period_covered": {
                    "start": artifact.period_start.isoformat() if artifact.period_start else None,
                    "end": artifact.period_end.isoformat() if artifact.period_end else None,
                },
                "approval": {
                    "status": artifact.approval_status.value,
                    "approved_by": (
                        latest_approval.user.name if latest_approval and latest_approval.user else None
                    ),
                    "approved_at": (
                        latest_approval.approved_at.isoformat() if latest_approval else None
                    ),
                    "signature_hash": latest_approval.signature_hash if latest_approval else None,
                },
                "control_mappings": [
                    {
                        "control_id": m.control_id,
                        "rationale": m.mapping_rationale,
                        "source": m.mapping_source.value,
                        "confidence": m.confidence_score,
                    }
                    for m in artifact.control_mappings
                ],
            }
            manifest["evidence_items"].append(evidence_item)

            # Update summary
            manifest["summary"]["total_items"] += 1

            if artifact.approval_status == ApprovalStatus.APPROVED:
                manifest["summary"]["approved_items"] += 1
            else:
                manifest["summary"]["pending_items"] += 1

            # Count by source
            source = artifact.source_system
            manifest["summary"]["by_source"][source] = (
                manifest["summary"]["by_source"].get(source, 0) + 1
            )

            # Count by type
            atype = artifact.artifact_type.value
            manifest["summary"]["by_type"][atype] = (
                manifest["summary"]["by_type"].get(atype, 0) + 1
            )

        return manifest

    def generate_folder_structure(self, packet: EvidencePacket) -> dict[str, str]:
        """Generate folder structure for Drive export.

        Returns dict mapping relative paths to content descriptions.
        """
        structure = {
            f"{packet.control_id}/": "Control evidence folder",
            f"{packet.control_id}/manifest.json": "Evidence manifest with provenance",
            f"{packet.control_id}/narrative.md": "Control narrative document",
            f"{packet.control_id}/evidence/": "Evidence artifacts",
        }

        for item in packet.items:
            artifact = item.artifact
            # Create subfolder by source system
            source_folder = f"{packet.control_id}/evidence/{artifact.source_system}/"
            structure[source_folder] = f"Evidence from {artifact.source_system}"

            # Add artifact file
            safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in artifact.title)
            artifact_path = f"{source_folder}{safe_title[:50]}.json"
            structure[artifact_path] = f"Artifact: {artifact.title}"

        return structure

    async def mark_exported(self, packet: EvidencePacket, drive_folder_url: str | None = None) -> None:
        """Mark packet as exported."""
        packet.status = PacketStatus.EXPORTED
        packet.exported_at = datetime.now(timezone.utc)
        if drive_folder_url:
            packet.drive_folder_url = drive_folder_url
        await self.db.flush()
