"""FastAPI routes for the Wowasi_ya API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from wowasi_ya.api.auth import RequireAuth, User
from wowasi_ya.config import Settings, get_settings
from wowasi_ya.core import (
    AgentDiscoveryService,
    DocumentExtractor,
    DocumentGenerator,
    OutputManager,
    PrivacyLayer,
    QualityChecker,
    ResearchEngine,
)
from wowasi_ya.core.next_steps import NextStepsEngine, get_next_steps_engine
from wowasi_ya.core.privacy import PrivacyScanResult
from wowasi_ya.models.agent import AgentDefinition, DomainMatch
from wowasi_ya.models.document import DocumentType, GeneratedProject
from wowasi_ya.models.next_steps import (
    ProjectNextStep,
    ProjectProgress,
    StepStatus,
)
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


# Document upload constraints
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
}


class DocumentExtractResponse(BaseModel):
    """Response from document extraction."""

    extracted_text: str = Field(..., description="Extracted text content")
    char_count: int = Field(..., description="Number of characters extracted")
    page_count: int | None = Field(default=None, description="Number of pages (for PDFs)")
    was_truncated: bool = Field(default=False, description="Whether text was truncated")
    truncation_reason: str | None = Field(default=None, description="Reason for truncation")
    warnings: list[str] = Field(default_factory=list, description="Extraction warnings")
    privacy_scan: PrivacyScanResult = Field(..., description="Privacy scan results")
    suggested_description: str = Field(..., description="Suggested description (first 2000 chars)")
    suggested_additional_context: str | None = Field(
        default=None,
        description="Suggested additional context (remainder after 2000 chars)",
    )


# Initialize services
discovery_service = AgentDiscoveryService()
privacy_layer = PrivacyLayer()
quality_checker = QualityChecker()
document_extractor = DocumentExtractor()


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


@router.post("/extract-document", response_model=DocumentExtractResponse)
async def extract_document(
    file: Annotated[UploadFile, File(description="Document to extract text from (PDF, DOCX, TXT)")],
) -> DocumentExtractResponse:
    """Extract text from an uploaded document.

    Supports PDF, DOCX, and TXT files up to 10MB.
    Returns extracted text with privacy scan results for review before project creation.

    The extracted text is automatically split:
    - First 2000 chars -> suggested_description
    - Remainder -> suggested_additional_context
    """
    from io import BytesIO

    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Validate file extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Supported types: PDF, DOCX, TXT",
        )

    # Read file content and check size
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Extract text
    try:
        result = document_extractor.extract(BytesIO(contents), file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Run privacy scan on extracted text
    privacy_scan = privacy_layer.scan(result.text)

    # Split into description and additional_context
    description_limit = 2000
    if result.char_count <= description_limit:
        suggested_description = result.text
        suggested_additional_context = None
    else:
        suggested_description = result.text[:description_limit]
        suggested_additional_context = result.text[description_limit:]

    return DocumentExtractResponse(
        extracted_text=result.text,
        char_count=result.char_count,
        page_count=result.page_count,
        was_truncated=result.was_truncated,
        truncation_reason=result.truncation_reason,
        warnings=result.warnings,
        privacy_scan=privacy_scan,
        suggested_description=suggested_description,
        suggested_additional_context=suggested_additional_context,
    )


@router.post("/projects", response_model=ProjectCreateResponse)
async def create_project(
    project: ProjectInput,
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


class PublishToOutlineRequest(BaseModel):
    """Request to publish project to Outline Wiki."""

    enable_sharing: bool = Field(
        default=False,
        description="Enable public sharing link for the collection",
    )


class PublishToOutlineResponse(BaseModel):
    """Response from publishing to Outline Wiki."""

    project_id: str
    collection_url: str
    collection_id: str
    document_urls: list[str]
    public_url: str | None = None
    message: str


@router.post(
    "/projects/{project_id}/publish-to-outline",
    response_model=PublishToOutlineResponse,
)
async def publish_to_outline(
    project_id: str,
    request: PublishToOutlineRequest,
    user: RequireAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublishToOutlineResponse:
    """Publish a completed project to Outline Wiki.

    Creates a collection in Outline and uploads all documents.
    Only available after generation is complete.
    """
    from wowasi_ya.core.outline import OutlinePublisher
    from wowasi_ya.models.document import Document, GeneratedProject

    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    if state.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Project not completed. Current status: {state.status}",
        )

    # Check if Outline is configured
    if not settings.outline_api_key:
        raise HTTPException(
            status_code=500,
            detail="Outline API key not configured. Set OUTLINE_API_KEY environment variable.",
        )

    # Reconstruct GeneratedProject from stored data
    documents = [Document(**d) for d in state.generated_documents]
    generated_project = GeneratedProject(
        project_name=state.input.name,
        project_area=state.input.area or "04_Iyeska",
        documents=documents,
    )

    # Publish to Outline
    try:
        publisher = OutlinePublisher(settings=settings)
        result = await publisher.publish(
            generated_project,
            enable_sharing=request.enable_sharing,
        )

        # Store Outline URLs in project state
        outline_urls = [result.collection.url] + [d.url for d in result.documents]
        state.output_paths.extend([f"outline:{url}" for url in outline_urls])

        return PublishToOutlineResponse(
            project_id=project_id,
            collection_url=result.collection.url,
            collection_id=result.collection.id,
            document_urls=[d.url for d in result.documents],
            public_url=result.public_url,
            message=f"Successfully published {len(result.documents)} documents to Outline",
        )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish to Outline: {e}",
        ) from e


@router.get("/projects")
async def list_projects() -> list[dict]:
    """List all projects (public read access for portal)."""
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


# ============================================================================
# Next Steps API Endpoints (Phase 3)
# ============================================================================


class CreateNextStepsRequest(BaseModel):
    """Request to create next steps for a project."""

    document_types: list[str] | None = Field(
        default=None,
        description="Document types to create steps for. If None, creates for all 15 types.",
    )


class CreateNextStepsResponse(BaseModel):
    """Response from creating next steps."""

    project_id: str
    steps_created: int
    message: str


class NextStepResponse(BaseModel):
    """Single next step response."""

    id: str
    project_id: str
    template_id: str
    document_type: str
    title: str
    description: str
    action_type: str
    action_config: dict
    is_required: bool
    status: str
    notes: str | None = None
    output_data: dict | None = None
    completed_at: str | None = None
    completed_by: str | None = None


class NextStepsListResponse(BaseModel):
    """Response for list of next steps."""

    project_id: str
    steps: list[NextStepResponse]
    total: int


class UpdateStepRequest(BaseModel):
    """Request to update a next step."""

    status: str | None = Field(
        default=None,
        description="New status: not_started, in_progress, completed, skipped",
    )
    notes: str | None = Field(default=None, description="Notes for this step")
    output_data: dict | None = Field(
        default=None,
        description="Form/checklist data for this step",
    )


class CompleteStepRequest(BaseModel):
    """Request to mark a step as completed."""

    completed_by: str | None = Field(
        default=None,
        description="Name or email of who completed the step",
    )
    output_data: dict | None = Field(
        default=None,
        description="Final form/checklist data",
    )


class SkipStepRequest(BaseModel):
    """Request to skip a step."""

    reason: str | None = Field(
        default=None,
        description="Reason for skipping this step",
    )


def _step_to_response(step: ProjectNextStep) -> NextStepResponse:
    """Convert ProjectNextStep to API response model."""
    return NextStepResponse(
        id=step.id,
        project_id=step.project_id,
        template_id=step.template_id,
        document_type=step.document_type.value,
        title=step.title,
        description=step.description,
        action_type=step.action_type.value,
        action_config=step.action_config,
        is_required=step.is_required,
        status=step.status.value,
        notes=step.notes,
        output_data=step.output_data,
        completed_at=step.completed_at.isoformat() if step.completed_at else None,
        completed_by=step.completed_by,
    )


@router.post(
    "/projects/{project_id}/next-steps",
    response_model=CreateNextStepsResponse,
)
async def create_next_steps(
    project_id: str,
    request: CreateNextStepsRequest,
    user: RequireAuth,
) -> CreateNextStepsResponse:
    """Create next steps for a project.

    This should be called after publishing to Outline to create
    actionable next steps for each document.
    """
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert string document types to enum if provided
    doc_types: list[DocumentType] | None = None
    if request.document_types:
        try:
            doc_types = [DocumentType(dt) for dt in request.document_types]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type: {e}",
            ) from e

    engine = get_next_steps_engine()
    steps = engine.create_steps_for_project(project_id, doc_types)

    return CreateNextStepsResponse(
        project_id=project_id,
        steps_created=len(steps),
        message=f"Created {len(steps)} next steps for project",
    )


@router.get(
    "/projects/{project_id}/next-steps",
    response_model=NextStepsListResponse,
)
async def get_next_steps(
    project_id: str,
    document_type: str | None = None,
) -> NextStepsListResponse:
    """Get all next steps for a project.

    Optionally filter by document type.
    """
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()

    # Convert document type filter if provided
    doc_type_filter: DocumentType | None = None
    if document_type:
        try:
            doc_type_filter = DocumentType(document_type)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type: {document_type}",
            ) from e

    steps = engine.get_steps(project_id, doc_type_filter)

    return NextStepsListResponse(
        project_id=project_id,
        steps=[_step_to_response(s) for s in steps],
        total=len(steps),
    )


@router.get(
    "/projects/{project_id}/next-steps/{step_id}",
    response_model=NextStepResponse,
)
async def get_next_step(
    project_id: str,
    step_id: str,
    user: RequireAuth,
) -> NextStepResponse:
    """Get a specific next step by ID."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()
    step = engine.get_step(step_id)

    if not step:
        raise HTTPException(status_code=404, detail="Next step not found")

    if step.project_id != project_id:
        raise HTTPException(status_code=404, detail="Next step not found in this project")

    return _step_to_response(step)


@router.patch(
    "/projects/{project_id}/next-steps/{step_id}",
    response_model=NextStepResponse,
)
async def update_next_step(
    project_id: str,
    step_id: str,
    request: UpdateStepRequest,
    user: RequireAuth,
) -> NextStepResponse:
    """Update a next step's status, notes, or output data."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()

    # Verify step exists and belongs to project
    existing = engine.get_step(step_id)
    if not existing or existing.project_id != project_id:
        raise HTTPException(status_code=404, detail="Next step not found in this project")

    # Convert status string to enum if provided
    status_enum: StepStatus | None = None
    if request.status:
        try:
            status_enum = StepStatus(request.status)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {request.status}. Valid values: not_started, in_progress, completed, skipped",
            ) from e

    step = engine.update_step(
        step_id,
        status=status_enum,
        notes=request.notes,
        output_data=request.output_data,
    )

    if not step:
        raise HTTPException(status_code=404, detail="Failed to update step")

    return _step_to_response(step)


@router.post(
    "/projects/{project_id}/next-steps/{step_id}/complete",
    response_model=NextStepResponse,
)
async def complete_next_step(
    project_id: str,
    step_id: str,
    request: CompleteStepRequest,
    user: RequireAuth,
) -> NextStepResponse:
    """Mark a next step as completed."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()

    # Verify step exists and belongs to project
    existing = engine.get_step(step_id)
    if not existing or existing.project_id != project_id:
        raise HTTPException(status_code=404, detail="Next step not found in this project")

    step = engine.complete_step(
        step_id,
        completed_by=request.completed_by,
        output_data=request.output_data,
    )

    if not step:
        raise HTTPException(status_code=404, detail="Failed to complete step")

    return _step_to_response(step)


@router.post(
    "/projects/{project_id}/next-steps/{step_id}/skip",
    response_model=NextStepResponse,
)
async def skip_next_step(
    project_id: str,
    step_id: str,
    request: SkipStepRequest,
    user: RequireAuth,
) -> NextStepResponse:
    """Mark a next step as skipped."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()

    # Verify step exists and belongs to project
    existing = engine.get_step(step_id)
    if not existing or existing.project_id != project_id:
        raise HTTPException(status_code=404, detail="Next step not found in this project")

    step = engine.skip_step(step_id, reason=request.reason)

    if not step:
        raise HTTPException(status_code=404, detail="Failed to skip step")

    return _step_to_response(step)


@router.get(
    "/projects/{project_id}/progress",
    response_model=ProjectProgress,
)
async def get_project_progress(
    project_id: str,
) -> ProjectProgress:
    """Get progress metrics for a project's next steps."""
    state = project_states.get(project_id)
    if not state:
        raise HTTPException(status_code=404, detail="Project not found")

    engine = get_next_steps_engine()
    progress = engine.get_progress(project_id)

    return progress
