"""Control mapping service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ControlMapping, EvidenceArtifact, MappingSource


# Mapping rules for Change Management control pack
CHANGE_MANAGEMENT_RULES = {
    "CC7.1": {
        "name": "Change Management",
        "artifact_types": ["pull_request", "jira_issue"],
        "keywords": ["change", "release", "deploy", "update"],
        "description": "Evidence of defined change management process",
    },
    "CC7.2": {
        "name": "Change Testing",
        "artifact_types": ["pull_request", "code_review"],
        "keywords": ["test", "review", "approve", "qa"],
        "description": "Evidence of changes tested before production",
    },
    "CC7.3": {
        "name": "Change Approval",
        "artifact_types": ["code_review", "jira_issue"],
        "keywords": ["approved", "approval", "authorized"],
        "description": "Evidence of management approval for changes",
    },
}


class MappingService:
    """Service for mapping artifacts to controls."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def auto_map_artifact(
        self,
        artifact: EvidenceArtifact,
    ) -> list[ControlMapping]:
        """Automatically map artifact to relevant controls based on rules."""
        mappings: list[ControlMapping] = []

        for control_id, rules in CHANGE_MANAGEMENT_RULES.items():
            score, rationale = self._evaluate_mapping(artifact, rules)

            if score > 0.5:  # Threshold for auto-mapping
                mapping = ControlMapping(
                    artifact_id=artifact.id,
                    control_id=control_id,
                    mapping_source=MappingSource.AUTO,
                    mapping_rationale=rationale,
                    confidence_score=score,
                )
                self.db.add(mapping)
                mappings.append(mapping)

        await self.db.flush()
        return mappings

    async def create_manual_mapping(
        self,
        artifact_id: UUID,
        control_id: str,
        rationale: str,
    ) -> ControlMapping:
        """Create a manual control mapping."""
        mapping = ControlMapping(
            artifact_id=artifact_id,
            control_id=control_id,
            mapping_source=MappingSource.MANUAL,
            mapping_rationale=rationale,
            confidence_score=1.0,  # Manual mappings are high confidence
        )
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_mappings_for_artifact(
        self,
        artifact_id: UUID,
    ) -> list[ControlMapping]:
        """Get all control mappings for an artifact."""
        result = await self.db.execute(
            select(ControlMapping).where(ControlMapping.artifact_id == artifact_id)
        )
        return list(result.scalars().all())

    async def get_artifacts_for_control(
        self,
        org_id: UUID,
        control_id: str,
    ) -> list[EvidenceArtifact]:
        """Get all artifacts mapped to a specific control."""
        result = await self.db.execute(
            select(EvidenceArtifact)
            .join(ControlMapping)
            .where(
                EvidenceArtifact.org_id == org_id,
                ControlMapping.control_id == control_id,
            )
        )
        return list(result.scalars().all())

    def _evaluate_mapping(
        self,
        artifact: EvidenceArtifact,
        rules: dict,
    ) -> tuple[float, str]:
        """Evaluate how well an artifact matches control rules.

        Returns:
            Tuple of (confidence_score, rationale)
        """
        score = 0.0
        rationale_parts = []

        # Check artifact type match
        if artifact.artifact_type.value in rules["artifact_types"]:
            score += 0.4
            rationale_parts.append(
                f"Artifact type '{artifact.artifact_type.value}' matches control requirements"
            )

        # Check keyword matches in title and content
        title_lower = artifact.title.lower()
        normalized_str = str(artifact.normalized_content).lower()

        keyword_matches = []
        for keyword in rules["keywords"]:
            if keyword in title_lower or keyword in normalized_str:
                keyword_matches.append(keyword)

        if keyword_matches:
            keyword_score = min(len(keyword_matches) * 0.15, 0.45)
            score += keyword_score
            rationale_parts.append(f"Contains relevant keywords: {', '.join(keyword_matches)}")

        # Check for PR with reviews (strong Change Management evidence)
        if artifact.artifact_type.value == "pull_request":
            normalized = artifact.normalized_content
            if normalized.get("merged"):
                score += 0.1
                rationale_parts.append("PR was merged (completed change)")
            if normalized.get("reviewers"):
                score += 0.05
                rationale_parts.append("PR has reviewers assigned")

        # Check for Jira issue with status changes
        if artifact.artifact_type.value == "jira_issue":
            normalized = artifact.normalized_content
            if normalized.get("changelog"):
                score += 0.1
                rationale_parts.append("Issue has status change history")

        rationale = "; ".join(rationale_parts) if rationale_parts else "No strong mapping indicators"
        return min(score, 1.0), rationale
