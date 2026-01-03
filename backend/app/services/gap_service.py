"""Gap detection service for identifying missing evidence."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ApprovalStatus, ControlMapping, EvidenceArtifact
from app.services.mapping_service import CHANGE_MANAGEMENT_RULES


@dataclass
class CoverageGap:
    """Represents a gap in evidence coverage."""

    control_id: str
    control_name: str
    gap_type: str  # missing_evidence, missing_approval, incomplete_period
    severity: str  # high, medium, low
    description: str
    recommended_action: str
    affected_period: tuple[date, date] | None = None


@dataclass
class PeriodCoverage:
    """Coverage statistics for a period."""

    control_id: str
    control_name: str
    period_start: date
    period_end: date
    months_covered: list[str]  # "2024-01", "2024-02", etc.
    months_missing: list[str]
    coverage_percentage: float
    artifact_count: int
    approved_count: int


class GapService:
    """Service for detecting evidence gaps and coverage issues."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_gaps(
        self,
        org_id: UUID,
        control_id: str,
        period_start: date,
        period_end: date,
    ) -> list[CoverageGap]:
        """Detect all gaps for a specific control in a period."""
        gaps: list[CoverageGap] = []
        control_rules = CHANGE_MANAGEMENT_RULES.get(control_id)

        if not control_rules:
            return gaps

        # Get artifacts mapped to this control
        artifacts = await self._get_control_artifacts(org_id, control_id, period_start, period_end)

        # Check for missing evidence types
        found_types = set(a.artifact_type.value for a in artifacts)
        required_types = set(control_rules["artifact_types"])
        missing_types = required_types - found_types

        if missing_types:
            gaps.append(
                CoverageGap(
                    control_id=control_id,
                    control_name=control_rules["name"],
                    gap_type="missing_evidence",
                    severity="high" if len(missing_types) > 1 else "medium",
                    description=f"Missing evidence types: {', '.join(missing_types)}",
                    recommended_action=f"Collect {', '.join(missing_types)} artifacts from source systems",
                )
            )

        # Check for unapproved artifacts
        unapproved = [a for a in artifacts if a.approval_status != ApprovalStatus.APPROVED]
        if unapproved:
            gaps.append(
                CoverageGap(
                    control_id=control_id,
                    control_name=control_rules["name"],
                    gap_type="missing_approval",
                    severity="medium",
                    description=f"{len(unapproved)} artifacts pending approval",
                    recommended_action="Review and approve pending artifacts before audit",
                )
            )

        # Check for period coverage gaps
        period_gaps = await self._find_period_gaps(
            artifacts, period_start, period_end
        )
        for gap_start, gap_end in period_gaps:
            gaps.append(
                CoverageGap(
                    control_id=control_id,
                    control_name=control_rules["name"],
                    gap_type="incomplete_period",
                    severity="high",  # Period gaps are serious for Type 2
                    description=f"No evidence from {gap_start} to {gap_end}",
                    recommended_action=f"Collect evidence covering {gap_start} to {gap_end}",
                    affected_period=(gap_start, gap_end),
                )
            )

        return gaps

    async def get_period_coverage(
        self,
        org_id: UUID,
        period_start: date,
        period_end: date,
    ) -> list[PeriodCoverage]:
        """Get coverage report for all controls in a period."""
        coverage_list: list[PeriodCoverage] = []

        for control_id, rules in CHANGE_MANAGEMENT_RULES.items():
            artifacts = await self._get_control_artifacts(
                org_id, control_id, period_start, period_end
            )

            # Calculate monthly coverage
            all_months = self._get_months_in_range(period_start, period_end)
            covered_months = set()

            for artifact in artifacts:
                if artifact.period_start and artifact.period_end:
                    artifact_months = self._get_months_in_range(
                        artifact.period_start, artifact.period_end
                    )
                    covered_months.update(artifact_months)

            months_covered = sorted(list(covered_months))
            months_missing = sorted(list(set(all_months) - covered_months))

            coverage_pct = (
                len(months_covered) / len(all_months) * 100
                if all_months
                else 0
            )

            approved_count = sum(
                1 for a in artifacts if a.approval_status == ApprovalStatus.APPROVED
            )

            coverage_list.append(
                PeriodCoverage(
                    control_id=control_id,
                    control_name=rules["name"],
                    period_start=period_start,
                    period_end=period_end,
                    months_covered=months_covered,
                    months_missing=months_missing,
                    coverage_percentage=round(coverage_pct, 1),
                    artifact_count=len(artifacts),
                    approved_count=approved_count,
                )
            )

        return coverage_list

    async def _get_control_artifacts(
        self,
        org_id: UUID,
        control_id: str,
        period_start: date,
        period_end: date,
    ) -> list[EvidenceArtifact]:
        """Get artifacts mapped to a control within a period."""
        result = await self.db.execute(
            select(EvidenceArtifact)
            .join(ControlMapping)
            .where(
                EvidenceArtifact.org_id == org_id,
                ControlMapping.control_id == control_id,
                EvidenceArtifact.period_start >= period_start,
                EvidenceArtifact.period_end <= period_end,
            )
        )
        return list(result.scalars().all())

    async def _find_period_gaps(
        self,
        artifacts: list[EvidenceArtifact],
        period_start: date,
        period_end: date,
    ) -> list[tuple[date, date]]:
        """Find gaps in period coverage.

        Returns list of (gap_start, gap_end) tuples.
        """
        if not artifacts:
            return [(period_start, period_end)]

        # Build coverage timeline
        all_months = self._get_months_in_range(period_start, period_end)
        covered_months = set()

        for artifact in artifacts:
            if artifact.period_start and artifact.period_end:
                artifact_months = self._get_months_in_range(
                    artifact.period_start, artifact.period_end
                )
                covered_months.update(artifact_months)

        # Find consecutive gaps
        gaps: list[tuple[date, date]] = []
        missing_months = sorted(set(all_months) - covered_months)

        if not missing_months:
            return gaps

        # Group consecutive months
        gap_start_month = missing_months[0]
        prev_month = missing_months[0]

        for month in missing_months[1:]:
            # Check if consecutive
            prev_date = date(int(prev_month[:4]), int(prev_month[5:7]), 1)
            curr_date = date(int(month[:4]), int(month[5:7]), 1)

            if (curr_date - prev_date).days > 32:  # Not consecutive
                # Close current gap
                gap_end = date(int(prev_month[:4]), int(prev_month[5:7]), 28)
                gap_start = date(int(gap_start_month[:4]), int(gap_start_month[5:7]), 1)
                gaps.append((gap_start, gap_end))

                # Start new gap
                gap_start_month = month

            prev_month = month

        # Close final gap
        gap_end = date(int(prev_month[:4]), int(prev_month[5:7]), 28)
        gap_start = date(int(gap_start_month[:4]), int(gap_start_month[5:7]), 1)
        gaps.append((gap_start, gap_end))

        return gaps

    def _get_months_in_range(self, start: date, end: date) -> list[str]:
        """Get list of months in YYYY-MM format between two dates."""
        months = []
        current = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)

        while current <= end_month:
            months.append(current.strftime("%Y-%m"))
            current += relativedelta(months=1)

        return months
