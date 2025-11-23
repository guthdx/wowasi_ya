"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1", tags=["projects"])

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
