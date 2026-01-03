"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import auth, integrations, artifacts, controls, packets, exports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AI-assisted evidence compiler for SOC 2 and ISO 27001 compliance",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["Evidence Artifacts"])
app.include_router(controls.router, prefix="/api/controls", tags=["Controls"])
app.include_router(packets.router, prefix="/api/packets", tags=["Evidence Packets"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
