"""Jira connector implementation."""

from datetime import datetime, timezone
from typing import AsyncIterator
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.connectors.base import (
    AuthenticationError,
    BaseConnector,
    ConnectionStatus,
    ConnectionTestResult,
    DateRange,
    OAuthCredentials,
    RawArtifact,
    ResourceFilter,
    ResourceRef,
)
from app.connectors.registry import register_connector

settings = get_settings()


@register_connector("jira")
class JiraConnector(BaseConnector):
    """Jira connector for fetching issues and transitions."""

    connector_type = "jira"

    JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
    JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    JIRA_API_URL = "https://api.atlassian.com"

    def __init__(self, credentials: OAuthCredentials | None = None):
        super().__init__(credentials)
        self._client: httpx.AsyncClient | None = None
        self._cloud_id: str | None = None

    async def _get_cloud_id(self) -> str:
        """Get Jira Cloud ID for API requests."""
        if self._cloud_id:
            return self._cloud_id

        self._ensure_authenticated()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.JIRA_API_URL}/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {self._credentials.access_token}"},
            )
            response.raise_for_status()
            resources = response.json()

            if not resources:
                raise AuthenticationError("No accessible Jira sites found")

            # Use first available site (could let user choose in UI)
            self._cloud_id = resources[0]["id"]
            return self._cloud_id

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            self._ensure_authenticated()
            cloud_id = await self._get_cloud_id()
            self._client = httpx.AsyncClient(
                base_url=f"{self.JIRA_API_URL}/ex/jira/{cloud_id}/rest/api/3",
                headers={
                    "Authorization": f"Bearer {self._credentials.access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def get_oauth_url(self, state: str) -> str:
        """Generate Jira OAuth authorization URL."""
        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.jira_client_id,
            "scope": "read:jira-work read:jira-user offline_access",
            "redirect_uri": f"{settings.app_url}/api/integrations/jira/callback",
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"{self.JIRA_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> OAuthCredentials:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.JIRA_TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "client_id": settings.jira_client_id,
                    "client_secret": settings.jira_client_secret,
                    "code": code,
                    "redirect_uri": f"{settings.app_url}/api/integrations/jira/callback",
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise AuthenticationError(data.get("error_description", data["error"]))

            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.now(timezone.utc).timestamp() + data["expires_in"]
                expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                token_type=data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scope=data.get("scope"),
            )

    async def refresh_access_token(self) -> OAuthCredentials:
        """Refresh expired access token."""
        if not self._credentials or not self._credentials.refresh_token:
            raise AuthenticationError("No refresh token available")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.JIRA_TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "client_id": settings.jira_client_id,
                    "client_secret": settings.jira_client_secret,
                    "refresh_token": self._credentials.refresh_token,
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.now(timezone.utc).timestamp() + data["expires_in"]
                expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)

            new_creds = OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", self._credentials.refresh_token),
                token_type=data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scope=data.get("scope"),
            )
            self._credentials = new_creds
            return new_creds

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection by fetching current user."""
        try:
            client = await self._get_client()
            response = await client.get("/myself")

            if response.status_code == 401:
                return ConnectionTestResult(
                    status=ConnectionStatus.AUTH_ERROR,
                    message="Invalid or expired Jira token",
                )

            response.raise_for_status()
            user_data = response.json()

            return ConnectionTestResult(
                status=ConnectionStatus.CONNECTED,
                message=f"Connected as {user_data.get('displayName', user_data.get('emailAddress'))}",
                details={
                    "account_id": user_data.get("accountId"),
                    "display_name": user_data.get("displayName"),
                },
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
        """List accessible Jira projects."""
        client = await self._get_client()
        projects: list[ResourceRef] = []

        response = await client.get("/project/search", params={"maxResults": 100})
        response.raise_for_status()
        data = response.json()

        for project in data.get("values", []):
            projects.append(
                ResourceRef(
                    id=project["id"],
                    name=f"{project['key']} - {project['name']}",
                    type="project",
                    url=project.get("self"),
                    extra={
                        "key": project["key"],
                        "project_type": project.get("projectTypeKey"),
                    },
                )
            )

        return projects[: filters.limit if filters else len(projects)]

    async def fetch_artifacts(
        self,
        resource_id: str,
        date_range: DateRange,
        artifact_types: list[str] | None = None,
    ) -> AsyncIterator[RawArtifact]:
        """Fetch Jira issues from a project."""
        client = await self._get_client()

        if artifact_types is None:
            artifact_types = ["jira_issue"]

        if "jira_issue" not in artifact_types:
            return

        # JQL query for issues in date range
        jql = (
            f"project = {resource_id} "
            f"AND created >= '{date_range.start}' "
            f"AND created <= '{date_range.end}' "
            f"ORDER BY created DESC"
        )

        start_at = 0
        max_results = 100

        while True:
            response = await client.get(
                "/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                    "expand": "changelog,transitions",
                    "fields": "*all",
                },
            )
            response.raise_for_status()
            data = response.json()

            issues = data.get("issues", [])
            if not issues:
                break

            for issue in issues:
                fields = issue.get("fields", {})
                created_at = datetime.fromisoformat(
                    fields.get("created", "").replace("Z", "+00:00")
                )

                yield RawArtifact(
                    source_system="jira",
                    source_object_id=issue["key"],
                    source_url=f"https://atlassian.net/browse/{issue['key']}",  # Will need cloud URL
                    source_created_at=created_at,
                    artifact_type="jira_issue",
                    title=f"{issue['key']}: {fields.get('summary', '')}",
                    raw_content=issue,
                    captured_at=datetime.now(timezone.utc),
                    period_start=created_at.date(),
                    period_end=created_at.date(),
                )

            start_at += max_results
            if start_at >= data.get("total", 0):
                break

    def get_artifact_url(self, artifact: RawArtifact) -> str:
        """Get deep link URL to Jira issue."""
        return artifact.source_url
