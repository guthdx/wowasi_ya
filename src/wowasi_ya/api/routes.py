"""FastAPI routes for the Wowasi_ya API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from wowasi_ya.api.auth import RequireAuth, User
from wowasi_ya.config import Settings, get_settings
from wowasi_ya.core import (
    AgentDiscoveryService,
    DocumentGenerator,
    OutputManager,
    PrivacyLayer,
    QualityChecker,
    ResearchEngine,
)
from wowasi_ya.core.privacy import PrivacyScanResult
from wowasi_ya.models.agent import AgentDefinition, DomainMatch
from wowasi_ya.models.document import GeneratedProject
from wowasi_ya.models.project import ProjectInput, ProjectState, ProjectStatus

router = APIRouter()

# In-memory storage for project states (replace with database in production)
project_states: dict[str, ProjectState] = {}


class ProjectCreateResponse(BaseModel):
    """Response when creating a new project."""

    project_id: str
    status: ProjectStatus
    message: str


class DiscoveryResponse(BaseModel):
    """Response from agent discovery phase."""

    project_id: str
    domains: list[DomainMatch]
    agents: list[AgentDefinition]
    privacy_scan: PrivacyScanResult


class ApprovalRequest(BaseModel):
    """Request to approve privacy flags and proceed."""

    approved: bool = True
    use_sanitized: bool = Field(
        default=True,
        description="Use sanitized text instead of original",
    )


class GenerationStatusResponse(BaseModel):
    """Response for generation status check."""

    project_id: str
    status: ProjectStatus
    phase: int
    documents_generated: int
    error: str | None = None


# Initialize services
discovery_service = AgentDiscoveryService()
privacy_layer = PrivacyLayer()
quality_checker = QualityChecker()


@router.get("/health")
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | dict]:
    """Health check endpoint with LLM provider status.

    Returns:
        System health including generation provider availability.
    """
    from wowasi_ya.core.llm_client import LlamaCPPClient

    health_info: dict[str, str | dict] = {
        "status": "healthy",
        "service": "wowasi_ya",
        "generation_provider": settings.generation_provider,
        "research_provider": settings.research_provider,
    }

    # Check Llama CPP availability if configured
    if settings.generation_provider == "llamacpp":
        llama_client = LlamaCPPClient(settings)
        try:
            is_available = await llama_client.health_check()
            await llama_client.close()

            health_info["llamacpp"] = {
                "available": is_available,
                "url": settings.llamacpp_base_url,
                "fallback_enabled": settings.llamacpp_fallback_to_claude,
            }

            if not is_available:
                health_info["llamacpp"]["message"] = (
                    "Mac Llama server unreachable. "
                    "Ensure Mac is online with Cloudflare tunnel running."
                )
                if settings.llamacpp_fallback_to_claude:
                    health_info["llamacpp"]["fallback_status"] = "Will use Claude"
        except Exception as e:
            health_info["llamacpp"] = {
                "available": False,
                "error": str(e),
                "fallback_enabled": settings.llamacpp_fallback_to_claude,
            }

    return health_info


@router.post("/projects", response_model=ProjectCreateResponse)
async def create_project(
    project: ProjectInput,
    user: RequireAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProjectCreateResponse:
    """Create a new project and start Phase 0 (Agent Discovery).

    This endpoint:
    1. Creates a new project record
    2. Runs local agent discovery (no API calls)
    3. Scans for privacy concerns
    4. Returns discovered agents and privacy flags for review
    """
    project_id = str(uuid.uuid4())

    # Create project state
    state = ProjectState(
        id=project_id,
        input=project,
        status=ProjectStatus.AGENT_DISCOVERY,
    )
    project_states[project_id] = state

    return ProjectCreateResponse(
        project_id=project_id,
        status=state.status,
        message="Project created. Use GET /projects/{id}/discovery to see results.",
    )


@router.get("/projects/{project_id}/discovery", response_model=DiscoveryResponse)
async def get_discovery_results(
    project_id: str,
    user: RequireAuth,
) -> DiscoveryResponse:
    """Get agent discovery and privacy scan results.

    Returns the discovered agents and any privacy flags that need review.
    """
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run discovery if not already done
    if not state.discovered_agents:
        domains, agents = discovery_service.discover(state.input)
        state.discovered_agents = [a.model_dump() for a in agents]

        # Store domain matches
        state.research_results["domains"] = [d.model_dump() for d in domains]

    # Run privacy scan
    text_to_scan = f"{state.input.name} {state.input.description} {state.input.additional_context or ''}"
    privacy_scan = privacy_layer.scan(text_to_scan)
    state.privacy_flags = [f.model_dump() for f in privacy_scan.flags]
    state.status = ProjectStatus.PRIVACY_REVIEW

    # Reconstruct models from stored data
    domains = [DomainMatch(**d) for d in state.research_results.get("domains", [])]
    agents = [AgentDefinition(**a) for a in state.discovered_agents]

    return DiscoveryResponse(
        project_id=project_id,
        domains=domains,
        agents=agents,
        privacy_scan=privacy_scan,
    )


@router.post("/projects/{project_id}/approve")
async def approve_privacy(
    project_id: str,
    approval: ApprovalRequest,
    user: RequireAuth,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """Approve privacy flags and start generation.

    This is the gate before any API calls are made.
    """
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    if state.status not in [ProjectStatus.PRIVACY_REVIEW, ProjectStatus.AWAITING_APPROVAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve project in status: {state.status}",
        )

    if not approval.approved:
        state.status = ProjectStatus.FAILED
        state.error = "Privacy approval denied by user"
        return {"status": "cancelled", "message": "Generation cancelled by user"}

    state.privacy_approved = True
    state.status = ProjectStatus.RESEARCHING

    # Start background generation
    background_tasks.add_task(
        run_generation_pipeline,
        project_id,
        settings,
        approval.use_sanitized,
    )

    return {
        "status": "started",
        "message": "Generation started. Check status at GET /projects/{id}/status",
    }


@router.get("/projects/{project_id}/status", response_model=GenerationStatusResponse)
async def get_project_status(
    project_id: str,
    user: RequireAuth,
) -> GenerationStatusResponse:
    """Get the current status of a project generation."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    return GenerationStatusResponse(
        project_id=project_id,
        status=state.status,
        phase=state.current_phase,
        documents_generated=len(state.generated_documents),
        error=state.error,
    )


@router.get("/projects/{project_id}/result")
async def get_project_result(
    project_id: str,
    user: RequireAuth,
) -> dict:
    """Get the generated project result.

    Only available after generation is complete.
    """
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    if state.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Project not completed. Current status: {state.status}",
        )

    return {
        "project_id": project_id,
        "project_name": state.input.name,
        "documents": state.generated_documents,
        "output_paths": state.output_paths,
        "quality_issues": state.quality_issues,
    }


@router.get("/projects")
async def list_projects(user: RequireAuth) -> list[dict]:
    """List all projects for the current user."""
    return [
        {
            "id": state.id,
            "name": state.input.name,
            "status": state.status,
            "created_at": state.created_at.isoformat(),
        }
        for state in project_states.values()
    ]


async def run_generation_pipeline(
    project_id: str,
    settings: Settings,
    use_sanitized: bool,
) -> None:
    """Run the full generation pipeline in background.

    Phases:
    1. Research (API calls with web search)
    2. Document generation (API calls)
    3. Quality check (local)
    4. Output (local)
    """
    state = project_states.get(project_id)
    if not state:
        return

    try:
        # Prepare context
        if use_sanitized:
            # Use sanitized text from privacy scan
            text_to_use = privacy_layer.scan(
                f"{state.input.name} {state.input.description} {state.input.additional_context or ''}"
            ).sanitized_text
        else:
            text_to_use = f"{state.input.name} {state.input.description} {state.input.additional_context or ''}"

        # Phase 1: Research
        state.status = ProjectStatus.RESEARCHING
        state.current_phase = 1

        research_engine = ResearchEngine(settings)
        agents = [AgentDefinition(**a) for a in state.discovered_agents]
        research_results = await research_engine.execute_all(agents, text_to_use)
        state.research_results["agent_results"] = [r.model_dump() for r in research_results]

        # Phase 2: Document Generation
        state.status = ProjectStatus.GENERATING
        state.current_phase = 2

        generator = DocumentGenerator(settings)
        generated_project = await generator.generate_all(state.input, research_results)
        state.generated_documents = [d.model_dump() for d in generated_project.documents]

        # Phase 3: Quality Check
        state.status = ProjectStatus.QUALITY_CHECK
        state.current_phase = 3

        quality_issues = quality_checker.check_project(generated_project)
        state.quality_issues = [
            {
                "document": i.document,
                "severity": i.severity.value,
                "message": i.message,
                "suggestion": i.suggestion,
            }
            for i in quality_issues
        ]

        # Phase 4: Output
        state.status = ProjectStatus.OUTPUTTING

        output_manager = OutputManager(settings)

        # Write to primary output format
        output_paths = await output_manager.write(
            generated_project,
            state.input.output_format,
        )
        state.output_paths = output_paths

        # Auto-sync to Google Drive if enabled
        if settings.enable_gdrive_sync and state.input.output_format != "gdrive":
            try:
                gdrive_paths = await output_manager.write(generated_project, "gdrive")
                # Add gdrive paths to output for tracking
                state.output_paths.extend([f"gdrive:{p}" for p in gdrive_paths])
            except Exception as e:
                # Don't fail the whole operation if gdrive sync fails
                print(f"⚠ Warning: Google Drive sync failed: {e}")

        # Complete
        state.status = ProjectStatus.COMPLETED

    except Exception as e:
        state.status = ProjectStatus.FAILED
        state.error = str(e)
