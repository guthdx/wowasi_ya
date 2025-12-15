"""Project input and status models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Status of a project generation request."""

    PENDING = "pending"
    AGENT_DISCOVERY = "agent_discovery"
    PRIVACY_REVIEW = "privacy_review"
    AWAITING_APPROVAL = "awaiting_approval"
    RESEARCHING = "researching"
    GENERATING = "generating"
    QUALITY_CHECK = "quality_check"
    OUTPUTTING = "outputting"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectInput(BaseModel):
    """Input model for creating a new project."""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Detailed project description",
    )
    area: str = Field(
        default="04_Iyeska",
        description="Project area/category (e.g., 01_Personal, 02_MBIRI, 03_NativeBio, 04_Iyeska, 05_ProjectH3LP)",
    )
    additional_context: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional additional context or requirements",
    )
    output_format: str = Field(
        default="filesystem",
        description="Output format: filesystem, obsidian, or git",
    )


class ProjectState(BaseModel):
    """Current state of a project generation."""

    id: str = Field(..., description="Unique project ID")
    input: ProjectInput
    status: ProjectStatus = ProjectStatus.PENDING
    current_phase: int = Field(default=0, ge=0, le=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None

    # Phase outputs
    discovered_agents: list[Any] = Field(default_factory=list)
    privacy_flags: list[Any] = Field(default_factory=list)
    privacy_approved: bool = False
    research_results: dict[str, Any] = Field(default_factory=dict)
    generated_documents: list[Any] = Field(default_factory=list)
    quality_issues: list[Any] = Field(default_factory=list)
    output_paths: list[str] = Field(default_factory=list)
