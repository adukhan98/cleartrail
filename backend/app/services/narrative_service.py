"""AI narrative generation service."""

from datetime import datetime, timezone

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.packet import EvidencePacket, PacketStatus

settings = get_settings()


NARRATIVE_SYSTEM_PROMPT = """You are a compliance documentation expert helping generate evidence narratives for SOC 2 audits.

Your task is to create a clear, factual narrative that explains how the provided evidence demonstrates the control is operating effectively.

Guidelines:
1. Be factual and specific - cite actual artifact details (dates, approvers, ticket numbers)
2. Use professional, audit-appropriate language
3. Explain HOW the evidence demonstrates control effectiveness
4. Never fabricate or assume details not present in the evidence
5. Structure the narrative logically (introduction, evidence walkthrough, conclusion)
6. Keep the narrative concise but comprehensive

The narrative should be directly usable in an audit package without modification."""


NARRATIVE_USER_PROMPT = """Generate a compliance narrative for the following evidence packet:

**Control**: {control_id} - {control_title}
**Audit Period**: {period_start} to {period_end}

**Evidence Artifacts**:
{artifacts_summary}

Please write a professional narrative that:
1. Introduces the control objective
2. Walks through each piece of evidence and explains what it demonstrates
3. Concludes with how the evidence collectively demonstrates the control is operating effectively

Include specific details from the artifacts (dates, names, ticket numbers, etc.) to ensure traceability."""


class NarrativeService:
    """Service for generating AI narratives with provenance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def generate_narrative(
        self,
        packet: EvidencePacket,
        control_title: str,
    ) -> str:
        """Generate AI narrative for evidence packet.

        Args:
            packet: Evidence packet with loaded items
            control_title: Human-readable control title

        Returns:
            Generated narrative text
        """
        # Build artifacts summary from packet items
        artifacts_summary = self._build_artifacts_summary(packet)

        # Generate narrative using OpenAI
        client = self._get_client()

        user_prompt = NARRATIVE_USER_PROMPT.format(
            control_id=packet.control_id,
            control_title=control_title,
            period_start=packet.period_start.isoformat(),
            period_end=packet.period_end.isoformat(),
            artifacts_summary=artifacts_summary,
        )

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Lower temperature for factual content
            max_tokens=2000,
        )

        narrative = response.choices[0].message.content or ""

        # Update packet with generated narrative
        packet.ai_narrative = narrative
        packet.narrative_generated_at = datetime.now(timezone.utc)
        packet.status = PacketStatus.NARRATIVE_READY

        await self.db.flush()
        return narrative

    def _build_artifacts_summary(self, packet: EvidencePacket) -> str:
        """Build a summary of artifacts for the prompt."""
        summaries = []

        for i, item in enumerate(packet.items, 1):
            artifact = item.artifact
            normalized = artifact.normalized_content

            summary_parts = [
                f"**Artifact {i}: {artifact.title}**",
                f"- Type: {artifact.artifact_type.value}",
                f"- Source: {artifact.source_system} ({artifact.source_object_id})",
                f"- Date: {artifact.source_created_at.date() if artifact.source_created_at else 'Unknown'}",
                f"- URL: {artifact.source_url}",
            ]

            # Add type-specific details
            if artifact.artifact_type.value == "pull_request":
                summary_parts.append(f"- Author: {normalized.get('author', {}).get('login', 'Unknown')}")
                summary_parts.append(f"- Merged: {normalized.get('merged', False)}")
                if normalized.get('merged_at'):
                    summary_parts.append(f"- Merged At: {normalized.get('merged_at')}")

            elif artifact.artifact_type.value == "code_review":
                summary_parts.append(f"- Reviewer: {normalized.get('reviewer', {}).get('login', 'Unknown')}")
                summary_parts.append(f"- State: {normalized.get('state', 'Unknown')}")

            elif artifact.artifact_type.value == "jira_issue":
                summary_parts.append(f"- Status: {normalized.get('status', {}).get('name', 'Unknown')}")
                summary_parts.append(f"- Assignee: {normalized.get('assignee', {}).get('display_name', 'Unassigned')}")

            summaries.append("\n".join(summary_parts))

        return "\n\n".join(summaries)

    async def regenerate_narrative(
        self,
        packet: EvidencePacket,
        control_title: str,
        feedback: str,
    ) -> str:
        """Regenerate narrative incorporating feedback."""
        # Add feedback to the prompt
        artifacts_summary = self._build_artifacts_summary(packet)

        client = self._get_client()

        user_prompt = NARRATIVE_USER_PROMPT.format(
            control_id=packet.control_id,
            control_title=control_title,
            period_start=packet.period_start.isoformat(),
            period_end=packet.period_end.isoformat(),
            artifacts_summary=artifacts_summary,
        )

        # Include previous narrative and feedback
        user_prompt += f"\n\n**Previous Narrative** (rejected):\n{packet.ai_narrative}"
        user_prompt += f"\n\n**Feedback for improvement**:\n{feedback}"
        user_prompt += "\n\nPlease generate an improved narrative addressing the feedback."

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        narrative = response.choices[0].message.content or ""

        packet.ai_narrative = narrative
        packet.narrative_generated_at = datetime.now(timezone.utc)
        packet.status = PacketStatus.NARRATIVE_READY

        await self.db.flush()
        return narrative
