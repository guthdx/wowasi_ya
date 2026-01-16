"""Document generation models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents in the 15-document template."""

    README = "README"
    PROJECT_BRIEF = "Project-Brief"
    GLOSSARY = "Glossary"
    CONTEXT_BACKGROUND = "Context-and-Background"
    STAKEHOLDER_NOTES = "Stakeholder-Notes"
    GOALS_SUCCESS = "Goals-and-Success-Criteria"
    SCOPE_BOUNDARIES = "Scope-and-Boundaries"
    INITIAL_BUDGET = "Initial-Budget"
    TIMELINE_MILESTONES = "Timeline-and-Milestones"
    RISKS_ASSUMPTIONS = "Risks-and-Assumptions"
    PROCESS_WORKFLOW = "Process-Workflow"
    SOPS = "SOPs"
    TASK_BACKLOG = "Task-Backlog"
    MEETING_NOTES = "Meeting-Notes"
    STATUS_UPDATES = "Status-Updates"


class Document(BaseModel):
    """A generated document."""

    type: DocumentType
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Markdown content")
    folder: str = Field(..., description="Target folder (e.g., '00-Overview')")
    filename: str = Field(..., description="Output filename")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = Field(default=0)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)


class DocumentBatch(BaseModel):
    """A batch of documents to generate together."""

    batch_number: int = Field(..., ge=1, le=5)
    document_types: list[DocumentType]
    depends_on: list[int] = Field(
        default_factory=list,
        description="Batch numbers this batch depends on",
    )


class GeneratedProject(BaseModel):
    """Complete generated project with all documents."""

    project_name: str
    project_area: str = Field(default="04_Iyeska", description="Project area/category")
    documents: list[Document] = Field(default_factory=list)
    total_word_count: int = Field(default=0)
    generation_time_seconds: float = Field(default=0.0)
    output_paths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Token usage for cost tracking
    total_input_tokens: int = Field(default=0, description="Total input tokens used")
    total_output_tokens: int = Field(default=0, description="Total output tokens used")


# Document batch definitions (from Process-Workflow.md)
DOCUMENT_BATCHES = [
    DocumentBatch(
        batch_number=1,
        document_types=[
            DocumentType.README,
            DocumentType.PROJECT_BRIEF,
            DocumentType.GLOSSARY,
        ],
        depends_on=[],
    ),
    DocumentBatch(
        batch_number=2,
        document_types=[
            DocumentType.CONTEXT_BACKGROUND,
            DocumentType.STAKEHOLDER_NOTES,
        ],
        depends_on=[1],
    ),
    DocumentBatch(
        batch_number=3,
        document_types=[
            DocumentType.GOALS_SUCCESS,
            DocumentType.SCOPE_BOUNDARIES,
            DocumentType.INITIAL_BUDGET,
            DocumentType.TIMELINE_MILESTONES,
            DocumentType.RISKS_ASSUMPTIONS,
        ],
        depends_on=[1, 2],
    ),
    DocumentBatch(
        batch_number=4,
        document_types=[
            DocumentType.PROCESS_WORKFLOW,
            DocumentType.SOPS,
            DocumentType.TASK_BACKLOG,
        ],
        depends_on=[3],
    ),
    DocumentBatch(
        batch_number=5,
        document_types=[
            DocumentType.MEETING_NOTES,
            DocumentType.STATUS_UPDATES,
        ],
        depends_on=[],
    ),
]
