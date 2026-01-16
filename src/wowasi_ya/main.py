"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from wowasi_ya import __version__
from wowasi_ya.api import router
from wowasi_ya.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"Starting Wowasi_ya v{__version__} in {settings.environment} mode")

    # Ensure output directory exists
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("Shutting down Wowasi_ya")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Wowasi_ya",
        description="AI-powered project documentation generator",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS middleware - allow portal and API domains
    allowed_origins = (
        ["*"]
        if settings.is_development
        else [
            "https://portal.iyeska.net",
            "https://wowasi.iyeska.net",
            "http://localhost:3003",  # Local Vite dev server
            "http://localhost:3000",  # Alternative dev port
            "http://portal.localhost",  # Traefik local development
        ]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1", tags=["projects"])

    # Serve portal from portal/dist (built React app)
    portal_dir = Path(__file__).parent.parent.parent / "portal" / "dist"
    if portal_dir.exists():
        # Mount assets folder for JS/CSS bundles
        assets_dir = portal_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # Serve static files from portal dist (images, etc.)
        @app.get("/vite.svg")
        async def serve_vite_svg() -> FileResponse:
            return FileResponse(str(portal_dir / "vite.svg"))

        @app.get("/iyeska-logo.png")
        async def serve_logo() -> FileResponse:
            return FileResponse(str(portal_dir / "iyeska-logo.png"))

        # SPA catch-all: serve index.html for all non-API routes
        # This enables React Router to handle client-side routing
        @app.get("/{path:path}")
        async def serve_spa(path: str) -> FileResponse:
            """Serve the portal SPA for all non-API routes."""
            # Check if it's a file that exists in portal dist
            file_path = portal_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            # Otherwise serve index.html for SPA routing
            return FileResponse(str(portal_dir / "index.html"))

        @app.get("/")
        async def read_root() -> FileResponse:
            """Serve the portal dashboard."""
            return FileResponse(str(portal_dir / "index.html"))

    return app


# Create app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "wowasi_ya.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
