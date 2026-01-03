"""AI narrative generation tasks."""

import asyncio
from uuid import UUID

from celery import shared_task

from app.database import async_session_maker
from app.models.packet import EvidencePacket
from app.services.mapping_service import CHANGE_MANAGEMENT_RULES
from app.services.narrative_service import NarrativeService


@shared_task(bind=True, max_retries=2)
def generate_packet_narrative(self, packet_id: str) -> dict:
    """Generate AI narrative for an evidence packet.

    Args:
        packet_id: UUID of the packet

    Returns:
        Dict with generation results
    """
    return asyncio.run(_generate_narrative_async(UUID(packet_id)))


async def _generate_narrative_async(packet_id: UUID) -> dict:
    """Async implementation of narrative generation."""
    async with async_session_maker() as db:
        # Get packet with items loaded
        packet = await db.get(EvidencePacket, packet_id)
        if not packet:
            return {"error": "Packet not found"}

        # Get control title
        control_rules = CHANGE_MANAGEMENT_RULES.get(packet.control_id, {})
        control_title = control_rules.get("name", packet.control_id)

        try:
            service = NarrativeService(db)
            narrative = await service.generate_narrative(packet, control_title)

            await db.commit()

            return {
                "status": "completed",
                "narrative_length": len(narrative),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def regenerate_packet_narrative(self, packet_id: str, feedback: str) -> dict:
    """Regenerate AI narrative with feedback.

    Args:
        packet_id: UUID of the packet
        feedback: User feedback for improvement

    Returns:
        Dict with generation results
    """
    return asyncio.run(_regenerate_narrative_async(UUID(packet_id), feedback))


async def _regenerate_narrative_async(packet_id: UUID, feedback: str) -> dict:
    """Async implementation of narrative regeneration."""
    async with async_session_maker() as db:
        packet = await db.get(EvidencePacket, packet_id)
        if not packet:
            return {"error": "Packet not found"}

        control_rules = CHANGE_MANAGEMENT_RULES.get(packet.control_id, {})
        control_title = control_rules.get("name", packet.control_id)

        try:
            service = NarrativeService(db)
            narrative = await service.regenerate_narrative(packet, control_title, feedback)

            await db.commit()

            return {
                "status": "completed",
                "narrative_length": len(narrative),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}
