"""GitHub connector implementation."""

from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from app.config import get_settings
from app.connectors.base import (
    AuthenticationError,
    BaseConnector,
    ConnectionStatus,
    ConnectionTestResult,
    DateRange,
    OAuthCredentials,
    RateLimitError,
    RawArtifact,
    ResourceFilter,
    ResourceRef,
)
from app.connectors.registry import register_connector

settings = get_settings()


@register_connector("github")
class GitHubConnector(BaseConnector):
    """GitHub connector for fetching PRs, commits, and reviews."""

    connector_type = "github"

    GITHUB_API_URL = "https://api.github.com"
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

    def __init__(self, credentials: OAuthCredentials | None = None):
        super().__init__(credentials)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            self._ensure_authenticated()
            self._client = httpx.AsyncClient(
                base_url=self.GITHUB_API_URL,
                headers={
                    "Authorization": f"Bearer {self._credentials.access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
        return self._client

    def get_oauth_url(self, state: str) -> str:
        """Generate GitHub OAuth authorization URL."""
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": f"{settings.app_url}/api/integrations/github/callback",
            "scope": "repo read:org",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.GITHUB_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> OAuthCredentials:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise AuthenticationError(data.get("error_description", data["error"]))

            return OAuthCredentials(
                access_token=data["access_token"],
                token_type=data.get("token_type", "bearer"),
                scope=data.get("scope"),
            )

    async def refresh_access_token(self) -> OAuthCredentials:
        """GitHub OAuth tokens don't expire, but apps can be revoked."""
        # GitHub personal access tokens and OAuth tokens don't have refresh
        # For GitHub Apps, we'd use JWT + installation tokens
        raise NotImplementedError("GitHub OAuth tokens don't support refresh")

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection by fetching authenticated user."""
        try:
            client = await self._get_client()
            response = await client.get("/user")

            if response.status_code == 401:
                return ConnectionTestResult(
                    status=ConnectionStatus.AUTH_ERROR,
                    message="Invalid or expired GitHub token",
                )

            if response.status_code == 403:
                return ConnectionTestResult(
                    status=ConnectionStatus.PERMISSION_ERROR,
                    message="Insufficient permissions",
                )

            response.raise_for_status()
            user_data = response.json()

            return ConnectionTestResult(
                status=ConnectionStatus.CONNECTED,
                message=f"Connected as {user_data['login']}",
                details={"login": user_data["login"], "name": user_data.get("name")},
            )

        except httpx.HTTPError as e:
            return ConnectionTestResult(
                status=ConnectionStatus.NETWORK_ERROR,
                message=f"Network error: {str(e)}",
            )

    async def list_resources(
        self,
        filters: ResourceFilter | None = None,
    ) -> list[ResourceRef]:
        """List accessible repositories."""
        client = await self._get_client()
        repos: list[ResourceRef] = []
        page = 1

        while True:
            response = await client.get(
                "/user/repos",
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for repo in data:
                repos.append(
                    ResourceRef(
                        id=str(repo["id"]),
                        name=repo["full_name"],
                        type="repository",
                        url=repo["html_url"],
                        extra={
                            "private": repo["private"],
                            "default_branch": repo["default_branch"],
                        },
                    )
                )

            if filters and len(repos) >= filters.limit:
                break

            page += 1

        return repos[: filters.limit if filters else len(repos)]

    async def fetch_artifacts(
        self,
        resource_id: str,
        date_range: DateRange,
        artifact_types: list[str] | None = None,
    ) -> AsyncIterator[RawArtifact]:
        """Fetch PRs and reviews from a repository."""
        client = await self._get_client()

        # Default to all artifact types if not specified
        if artifact_types is None:
            artifact_types = ["pull_request", "code_review"]

        # Fetch repository info first
        repo_response = await client.get(f"/repositories/{resource_id}")
        repo_response.raise_for_status()
        repo = repo_response.json()
        repo_full_name = repo["full_name"]

        if "pull_request" in artifact_types or "code_review" in artifact_types:
            # Fetch pull requests
            page = 1
            while True:
                pr_response = await client.get(
                    f"/repos/{repo_full_name}/pulls",
                    params={
                        "state": "all",
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": 100,
                        "page": page,
                    },
                )

                if pr_response.status_code == 403:
                    # Rate limit
                    retry_after = int(pr_response.headers.get("Retry-After", 60))
                    raise RateLimitError("GitHub rate limit exceeded", retry_after)

                pr_response.raise_for_status()
                prs = pr_response.json()

                if not prs:
                    break

                for pr in prs:
                    pr_date = datetime.fromisoformat(
                        pr["created_at"].replace("Z", "+00:00")
                    ).date()

                    if pr_date < date_range.start:
                        # PRs are sorted by updated, so we might miss some
                        continue
                    if pr_date > date_range.end:
                        continue

                    if "pull_request" in artifact_types:
                        yield RawArtifact(
                            source_system="github",
                            source_object_id=f"PR#{pr['number']}",
                            source_url=pr["html_url"],
                            source_created_at=datetime.fromisoformat(
                                pr["created_at"].replace("Z", "+00:00")
                            ),
                            artifact_type="pull_request",
                            title=pr["title"],
                            raw_content=pr,
                            captured_at=datetime.now(timezone.utc),
                            period_start=pr_date,
                            period_end=pr_date,
                        )

                    # Fetch reviews for this PR
                    if "code_review" in artifact_types:
                        review_response = await client.get(
                            f"/repos/{repo_full_name}/pulls/{pr['number']}/reviews"
                        )
                        if review_response.status_code == 200:
                            reviews = review_response.json()
                            for review in reviews:
                                if review["state"] in ("APPROVED", "CHANGES_REQUESTED"):
                                    review_date = datetime.fromisoformat(
                                        review["submitted_at"].replace("Z", "+00:00")
                                    ).date()
                                    yield RawArtifact(
                                        source_system="github",
                                        source_object_id=f"Review#{review['id']}",
                                        source_url=review["html_url"],
                                        source_created_at=datetime.fromisoformat(
                                            review["submitted_at"].replace("Z", "+00:00")
                                        ),
                                        artifact_type="code_review",
                                        title=f"Review on PR#{pr['number']}: {review['state']}",
                                        raw_content={
                                            "review": review,
                                            "pr_number": pr["number"],
                                            "pr_title": pr["title"],
                                        },
                                        captured_at=datetime.now(timezone.utc),
                                        period_start=review_date,
                                        period_end=review_date,
                                    )

                page += 1

    def get_artifact_url(self, artifact: RawArtifact) -> str:
        """Get deep link URL to GitHub artifact."""
        return artifact.source_url
