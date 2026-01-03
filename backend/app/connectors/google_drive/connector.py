"""Google Drive connector implementation."""

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


@register_connector("google_drive")
class GoogleDriveConnector(BaseConnector):
    """Google Drive connector for fetching documents and policies."""

    connector_type = "google_drive"

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    DRIVE_API_URL = "https://www.googleapis.com/drive/v3"

    # MIME types for supported document types
    MIME_TYPES = {
        "document": "application/vnd.google-apps.document",
        "spreadsheet": "application/vnd.google-apps.spreadsheet",
        "pdf": "application/pdf",
        "folder": "application/vnd.google-apps.folder",
    }

    def __init__(self, credentials: OAuthCredentials | None = None):
        super().__init__(credentials)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            self._ensure_authenticated()
            self._client = httpx.AsyncClient(
                base_url=self.DRIVE_API_URL,
                headers={
                    "Authorization": f"Bearer {self._credentials.access_token}",
                },
                timeout=30.0,
            )
        return self._client

    def get_oauth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ]
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": f"{settings.app_url}/api/integrations/google_drive/callback",
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"{self.GOOGLE_AUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> OAuthCredentials:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{settings.app_url}/api/integrations/google_drive/callback",
                },
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
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": self._credentials.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            data = response.json()

            expires_at = None
            if "expires_in" in data:
                expires_at = datetime.now(timezone.utc).timestamp() + data["expires_in"]
                expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)

            new_creds = OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=self._credentials.refresh_token,  # Google doesn't return new refresh token
                token_type=data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scope=data.get("scope"),
            )
            self._credentials = new_creds
            return new_creds

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection by fetching user info."""
        try:
            client = await self._get_client()
            response = await client.get("/about", params={"fields": "user"})

            if response.status_code == 401:
                return ConnectionTestResult(
                    status=ConnectionStatus.AUTH_ERROR,
                    message="Invalid or expired Google token",
                )

            response.raise_for_status()
            data = response.json()
            user = data.get("user", {})

            return ConnectionTestResult(
                status=ConnectionStatus.CONNECTED,
                message=f"Connected as {user.get('displayName', user.get('emailAddress'))}",
                details={
                    "email": user.get("emailAddress"),
                    "display_name": user.get("displayName"),
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
        """List accessible folders in Drive."""
        client = await self._get_client()
        folders: list[ResourceRef] = []

        # Query for folders only
        query = f"mimeType = '{self.MIME_TYPES['folder']}' and trashed = false"

        page_token = None
        while True:
            params = {
                "q": query,
                "fields": "nextPageToken, files(id, name, webViewLink, modifiedTime)",
                "pageSize": 100,
            }
            if page_token:
                params["pageToken"] = page_token

            response = await client.get("/files", params=params)
            response.raise_for_status()
            data = response.json()

            for file in data.get("files", []):
                folders.append(
                    ResourceRef(
                        id=file["id"],
                        name=file["name"],
                        type="folder",
                        url=file.get("webViewLink"),
                        extra={"modified_time": file.get("modifiedTime")},
                    )
                )

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return folders[: filters.limit if filters else len(folders)]

    async def fetch_artifacts(
        self,
        resource_id: str,
        date_range: DateRange,
        artifact_types: list[str] | None = None,
    ) -> AsyncIterator[RawArtifact]:
        """Fetch documents from a folder."""
        client = await self._get_client()

        if artifact_types is None:
            artifact_types = ["document", "policy"]

        # Query for documents in the folder within date range
        mime_types = [
            self.MIME_TYPES["document"],
            self.MIME_TYPES["spreadsheet"],
            self.MIME_TYPES["pdf"],
        ]
        mime_query = " or ".join(f"mimeType = '{mt}'" for mt in mime_types)

        query = (
            f"'{resource_id}' in parents "
            f"and ({mime_query}) "
            f"and trashed = false "
            f"and modifiedTime >= '{date_range.start}T00:00:00Z' "
            f"and modifiedTime <= '{date_range.end}T23:59:59Z'"
        )

        page_token = None
        while True:
            params = {
                "q": query,
                "fields": "nextPageToken, files(id, name, mimeType, webViewLink, createdTime, modifiedTime, owners, lastModifyingUser)",
                "pageSize": 100,
            }
            if page_token:
                params["pageToken"] = page_token

            response = await client.get("/files", params=params)
            response.raise_for_status()
            data = response.json()

            for file in data.get("files", []):
                created_at = datetime.fromisoformat(
                    file.get("createdTime", "").replace("Z", "+00:00")
                )
                modified_at = datetime.fromisoformat(
                    file.get("modifiedTime", "").replace("Z", "+00:00")
                )

                # Determine artifact type based on name patterns
                artifact_type = "document"
                if any(kw in file["name"].lower() for kw in ["policy", "procedure", "standard"]):
                    artifact_type = "policy"
                elif "meeting" in file["name"].lower() or "notes" in file["name"].lower():
                    artifact_type = "meeting_notes"

                yield RawArtifact(
                    source_system="google_drive",
                    source_object_id=file["id"],
                    source_url=file.get("webViewLink", ""),
                    source_created_at=created_at,
                    artifact_type=artifact_type,
                    title=file["name"],
                    raw_content={
                        "id": file["id"],
                        "name": file["name"],
                        "mimeType": file.get("mimeType"),
                        "webViewLink": file.get("webViewLink"),
                        "createdTime": file.get("createdTime"),
                        "modifiedTime": file.get("modifiedTime"),
                        "owners": file.get("owners", []),
                        "lastModifyingUser": file.get("lastModifyingUser"),
                    },
                    captured_at=datetime.now(timezone.utc),
                    period_start=modified_at.date(),
                    period_end=modified_at.date(),
                )

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    def get_artifact_url(self, artifact: RawArtifact) -> str:
        """Get deep link URL to Drive document."""
        return artifact.source_url
