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

    # Mount static files
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        # Serve index.html at root
        @app.get("/")
        async def read_root() -> FileResponse:
            """Serve the main web interface."""
            return FileResponse(str(static_dir / "index.html"))

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
