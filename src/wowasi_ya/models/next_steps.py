"""Next Steps models for project action tracking."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from wowasi_ya.models.document import DocumentType


class ActionType(str, Enum):
    """Types of actions for next steps."""

    GUIDANCE = "guidance"  # Read-only instructions
    CHECKLIST = "checklist"  # Interactive checkboxes
    FORM = "form"  # Input fields (assign owner, set date)


class StepStatus(str, Enum):
    """Status of a next step."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class NextStepTemplate(BaseModel):
    """Template for a next step associated with a document type.

    These are predefined and seeded at startup.
    """

    id: str = Field(..., description="Unique template ID")
    document_type: DocumentType
    step_order: int = Field(..., ge=1, description="Order within document type")
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    action_type: ActionType
    action_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific config (checklist items, form fields, etc.)",
    )
    is_required: bool = Field(default=False, description="Is this step required?")


class ProjectNextStep(BaseModel):
    """Instance of a next step for a specific project.

    Created when a project is published to track progress.
    """

    id: str = Field(..., description="Unique instance ID")
    project_id: str = Field(..., description="Associated project ID")
    template_id: str = Field(..., description="Reference to NextStepTemplate")
    document_type: DocumentType
    title: str = Field(..., description="Step title (copied from template)")
    description: str | None = None
    action_type: ActionType
    action_config: dict[str, Any] = Field(default_factory=dict)
    is_required: bool = False

    # Progress tracking
    status: StepStatus = Field(default=StepStatus.NOT_STARTED)
    completed_at: datetime | None = None
    completed_by: str | None = Field(default=None, description="Email or name")
    notes: str | None = None
    output_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Form responses, checklist items checked, etc.",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OutlineMapping(BaseModel):
    """Maps a wowasi project to its Outline collection and documents."""

    id: str = Field(..., description="Unique mapping ID")
    project_id: str = Field(..., description="Wowasi project ID")
    outline_collection_id: str = Field(..., description="Outline collection ID")
    outline_collection_url: str = Field(..., description="Outline collection URL")
    outline_document_ids: dict[str, str] = Field(
        default_factory=dict,
        description="Map of document_type -> outline_document_id",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectProgress(BaseModel):
    """Aggregated progress for a project."""

    project_id: str
    total_steps: int
    completed_steps: int
    in_progress_steps: int
    skipped_steps: int
    not_started_steps: int
    completion_percentage: float = Field(ge=0, le=100)
    required_steps_total: int
    required_steps_completed: int
    by_document_type: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="Progress breakdown by document type",
    )


# Predefined next step templates for all 15 document types
NEXT_STEP_TEMPLATES: list[dict[str, Any]] = [
    # Project Brief
    {
        "id": "brief-1",
        "document_type": DocumentType.PROJECT_BRIEF,
        "step_order": 1,
        "title": "Share with stakeholders for feedback",
        "description": "Send the project brief to key stakeholders and collect their feedback on scope, timeline, and objectives.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Identify stakeholders to share with",
                "Send brief via email or shared link",
                "Set feedback deadline",
                "Collect and document feedback",
            ]
        },
        "is_required": True,
    },
    {
        "id": "brief-2",
        "document_type": DocumentType.PROJECT_BRIEF,
        "step_order": 2,
        "title": "Identify gaps and questions",
        "description": "Review the brief for any missing information or areas that need clarification.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "gaps", "label": "Identified Gaps", "type": "textarea"},
                {"name": "questions", "label": "Questions to Answer", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "brief-3",
        "document_type": DocumentType.PROJECT_BRIEF,
        "step_order": 3,
        "title": "Schedule kickoff meeting",
        "description": "Set up a project kickoff meeting with the core team.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "meeting_date", "label": "Meeting Date", "type": "date"},
                {"name": "attendees", "label": "Attendees", "type": "text"},
                {"name": "location", "label": "Location/Link", "type": "text"},
            ]
        },
        "is_required": True,
    },
    # README
    {
        "id": "readme-1",
        "document_type": DocumentType.README,
        "step_order": 1,
        "title": "Verify all links work",
        "description": "Check that all internal and external links in the README are functional.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Test all document cross-references",
                "Verify external URLs are accessible",
                "Check contact information is current",
            ]
        },
        "is_required": False,
    },
    {
        "id": "readme-2",
        "document_type": DocumentType.README,
        "step_order": 2,
        "title": "Share with new team members",
        "description": "Use this document to onboard new team members to the project.",
        "action_type": ActionType.GUIDANCE,
        "action_config": {
            "instructions": "Share the README link with anyone joining the project. It serves as the central navigation hub for all project documentation."
        },
        "is_required": False,
    },
    {
        "id": "readme-3",
        "document_type": DocumentType.README,
        "step_order": 3,
        "title": "Set reminder to update quarterly",
        "description": "Schedule quarterly reviews to keep the README current.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "next_review", "label": "Next Review Date", "type": "date"},
                {"name": "reviewer", "label": "Assigned Reviewer", "type": "text"},
            ]
        },
        "is_required": False,
    },
    # Glossary
    {
        "id": "glossary-1",
        "document_type": DocumentType.GLOSSARY,
        "step_order": 1,
        "title": "Review with domain experts",
        "description": "Have subject matter experts validate terminology definitions.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "reviewers", "label": "Domain Experts", "type": "text"},
                {"name": "review_date", "label": "Review Completed", "type": "date"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "glossary-2",
        "document_type": DocumentType.GLOSSARY,
        "step_order": 2,
        "title": "Add organization-specific terms",
        "description": "Include any internal jargon or acronyms used by your organization.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Review for missing internal terms",
                "Add organization acronyms",
                "Include tribal/cultural terminology if applicable",
            ]
        },
        "is_required": False,
    },
    # Context & Background
    {
        "id": "context-1",
        "document_type": DocumentType.CONTEXT_BACKGROUND,
        "step_order": 1,
        "title": "Validate assumptions with stakeholders",
        "description": "Confirm the background information and assumptions are accurate.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Share with stakeholders for validation",
                "Mark assumptions as confirmed or updated",
                "Document any corrections needed",
            ]
        },
        "is_required": True,
    },
    {
        "id": "context-2",
        "document_type": DocumentType.CONTEXT_BACKGROUND,
        "step_order": 2,
        "title": "Flag outdated information",
        "description": "Identify any information that may become stale and needs regular updates.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "outdated_sections", "label": "Sections to Monitor", "type": "textarea"},
                {"name": "update_frequency", "label": "Update Frequency", "type": "text"},
            ]
        },
        "is_required": False,
    },
    # Stakeholder Notes
    {
        "id": "stakeholder-1",
        "document_type": DocumentType.STAKEHOLDER_NOTES,
        "step_order": 1,
        "title": "Assign communication owners",
        "description": "Assign team members to manage relationships with each stakeholder group.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "assignments", "label": "Stakeholder-Owner Assignments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "stakeholder-2",
        "document_type": DocumentType.STAKEHOLDER_NOTES,
        "step_order": 2,
        "title": "Schedule introductory meetings",
        "description": "Set up initial meetings with key stakeholders.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Identify priority stakeholders",
                "Schedule meetings",
                "Prepare meeting agendas",
                "Document meeting outcomes",
            ]
        },
        "is_required": False,
    },
    # Goals & Success Criteria
    {
        "id": "goals-1",
        "document_type": DocumentType.GOALS_SUCCESS,
        "step_order": 1,
        "title": "Assign metric owners",
        "description": "Assign team members responsible for tracking each success metric.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "metric_owners", "label": "Metric-Owner Assignments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "goals-2",
        "document_type": DocumentType.GOALS_SUCCESS,
        "step_order": 2,
        "title": "Set up tracking dashboard",
        "description": "Create a dashboard or spreadsheet to track progress toward goals.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Select tracking tool (spreadsheet, dashboard, etc.)",
                "Create tracking template",
                "Set up automated data collection if possible",
                "Share access with team",
            ]
        },
        "is_required": False,
    },
    {
        "id": "goals-3",
        "document_type": DocumentType.GOALS_SUCCESS,
        "step_order": 3,
        "title": "Define baseline measurements",
        "description": "Document current state metrics to measure progress against.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "baselines", "label": "Baseline Measurements", "type": "textarea"},
                {"name": "measurement_date", "label": "Measurement Date", "type": "date"},
            ]
        },
        "is_required": True,
    },
    # Scope & Boundaries
    {
        "id": "scope-1",
        "document_type": DocumentType.SCOPE_BOUNDARIES,
        "step_order": 1,
        "title": "Get formal sign-off",
        "description": "Obtain stakeholder approval on the defined scope and boundaries.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "approver", "label": "Approved By", "type": "text"},
                {"name": "approval_date", "label": "Approval Date", "type": "date"},
                {"name": "notes", "label": "Approval Notes", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "scope-2",
        "document_type": DocumentType.SCOPE_BOUNDARIES,
        "step_order": 2,
        "title": "Set up change request process",
        "description": "Establish a process for handling scope change requests.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Define change request template",
                "Identify approval authority",
                "Set response timeframes",
                "Communicate process to team",
            ]
        },
        "is_required": False,
    },
    # Timeline & Milestones
    {
        "id": "timeline-1",
        "document_type": DocumentType.TIMELINE_MILESTONES,
        "step_order": 1,
        "title": "Import to project management tool",
        "description": "Add milestones and tasks to your project management system.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "tool", "label": "PM Tool Used", "type": "text"},
                {"name": "link", "label": "Project Link", "type": "text"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "timeline-2",
        "document_type": DocumentType.TIMELINE_MILESTONES,
        "step_order": 2,
        "title": "Assign milestone owners",
        "description": "Assign team members responsible for each major milestone.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "assignments", "label": "Milestone-Owner Assignments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    # Initial Budget
    {
        "id": "budget-1",
        "document_type": DocumentType.INITIAL_BUDGET,
        "step_order": 1,
        "title": "Review with finance",
        "description": "Have finance team review and validate budget assumptions.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "reviewer", "label": "Finance Reviewer", "type": "text"},
                {"name": "review_date", "label": "Review Date", "type": "date"},
                {"name": "feedback", "label": "Feedback/Adjustments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "budget-2",
        "document_type": DocumentType.INITIAL_BUDGET,
        "step_order": 2,
        "title": "Identify funding sources",
        "description": "Document where funding will come from for each budget category.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "funding_sources", "label": "Funding Sources", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "budget-3",
        "document_type": DocumentType.INITIAL_BUDGET,
        "step_order": 3,
        "title": "Flag items needing quotes",
        "description": "Identify budget line items that need vendor quotes or estimates.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "List items needing quotes",
                "Request quotes from vendors",
                "Update budget with actual figures",
            ]
        },
        "is_required": False,
    },
    # Risks & Assumptions
    {
        "id": "risks-1",
        "document_type": DocumentType.RISKS_ASSUMPTIONS,
        "step_order": 1,
        "title": "Assign risk owners",
        "description": "Assign team members to monitor and mitigate each identified risk.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "risk_owners", "label": "Risk-Owner Assignments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "risks-2",
        "document_type": DocumentType.RISKS_ASSUMPTIONS,
        "step_order": 2,
        "title": "Schedule risk review meetings",
        "description": "Set up recurring meetings to review risk status.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "frequency", "label": "Meeting Frequency", "type": "text"},
                {"name": "first_meeting", "label": "First Meeting Date", "type": "date"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "risks-3",
        "document_type": DocumentType.RISKS_ASSUMPTIONS,
        "step_order": 3,
        "title": "Prioritize mitigation actions",
        "description": "Rank risks by severity and begin mitigation for highest priority items.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Rank risks by impact and probability",
                "Identify top 3 risks",
                "Begin mitigation for critical risks",
                "Document mitigation progress",
            ]
        },
        "is_required": True,
    },
    # Process Workflow
    {
        "id": "workflow-1",
        "document_type": DocumentType.PROCESS_WORKFLOW,
        "step_order": 1,
        "title": "Walk through with team",
        "description": "Review the workflow with the team to ensure understanding and buy-in.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Schedule walkthrough session",
                "Present workflow to team",
                "Collect questions and concerns",
                "Update based on feedback",
            ]
        },
        "is_required": True,
    },
    {
        "id": "workflow-2",
        "document_type": DocumentType.PROCESS_WORKFLOW,
        "step_order": 2,
        "title": "Identify automation opportunities",
        "description": "Look for workflow steps that could be automated.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "automation_candidates", "label": "Steps to Automate", "type": "textarea"},
                {"name": "tools", "label": "Potential Tools", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
    # SOPs
    {
        "id": "sops-1",
        "document_type": DocumentType.SOPS,
        "step_order": 1,
        "title": "Assign procedure owners",
        "description": "Assign team members responsible for maintaining each SOP.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "sop_owners", "label": "SOP-Owner Assignments", "type": "textarea"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "sops-2",
        "document_type": DocumentType.SOPS,
        "step_order": 2,
        "title": "Schedule training sessions",
        "description": "Plan training for team members who will follow these procedures.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "training_date", "label": "Training Date", "type": "date"},
                {"name": "trainer", "label": "Trainer", "type": "text"},
                {"name": "attendees", "label": "Attendees", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "sops-3",
        "document_type": DocumentType.SOPS,
        "step_order": 3,
        "title": "Test procedures",
        "description": "Run through procedures to verify they work as documented.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Select procedures to test",
                "Perform dry run",
                "Document issues found",
                "Update procedures as needed",
            ]
        },
        "is_required": False,
    },
    # Task Backlog
    {
        "id": "backlog-1",
        "document_type": DocumentType.TASK_BACKLOG,
        "step_order": 1,
        "title": "Import to task management tool",
        "description": "Add backlog items to your project management or task tracking system.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "tool", "label": "Task Tool Used", "type": "text"},
                {"name": "link", "label": "Board/Project Link", "type": "text"},
            ]
        },
        "is_required": False,
    },
    {
        "id": "backlog-2",
        "document_type": DocumentType.TASK_BACKLOG,
        "step_order": 2,
        "title": "Assign initial tasks",
        "description": "Assign the highest priority tasks to team members.",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Review task priorities",
                "Assign top tasks",
                "Set due dates",
                "Communicate assignments to team",
            ]
        },
        "is_required": True,
    },
    {
        "id": "backlog-3",
        "document_type": DocumentType.TASK_BACKLOG,
        "step_order": 3,
        "title": "Schedule sprint planning",
        "description": "Set up the first sprint or iteration planning session.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "planning_date", "label": "Planning Date", "type": "date"},
                {"name": "sprint_length", "label": "Sprint Length", "type": "text"},
            ]
        },
        "is_required": False,
    },
    # Meeting Notes
    {
        "id": "meetings-1",
        "document_type": DocumentType.MEETING_NOTES,
        "step_order": 1,
        "title": "Schedule recurring meetings",
        "description": "Set up regular project meetings (standups, status, reviews).",
        "action_type": ActionType.CHECKLIST,
        "action_config": {
            "items": [
                "Define meeting types needed",
                "Set recurring schedule",
                "Send calendar invites",
                "Share meeting template with team",
            ]
        },
        "is_required": True,
    },
    {
        "id": "meetings-2",
        "document_type": DocumentType.MEETING_NOTES,
        "step_order": 2,
        "title": "Assign note-taker rotation",
        "description": "Establish who will take notes at each meeting.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "rotation", "label": "Note-taker Rotation", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
    # Status Updates
    {
        "id": "status-1",
        "document_type": DocumentType.STATUS_UPDATES,
        "step_order": 1,
        "title": "Set reporting cadence",
        "description": "Define how often status reports will be sent.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "frequency", "label": "Report Frequency", "type": "text"},
                {"name": "day", "label": "Day of Week/Month", "type": "text"},
                {"name": "owner", "label": "Report Owner", "type": "text"},
            ]
        },
        "is_required": True,
    },
    {
        "id": "status-2",
        "document_type": DocumentType.STATUS_UPDATES,
        "step_order": 2,
        "title": "Identify report recipients",
        "description": "Create distribution list for status reports.",
        "action_type": ActionType.FORM,
        "action_config": {
            "fields": [
                {"name": "recipients", "label": "Report Recipients", "type": "textarea"},
            ]
        },
        "is_required": False,
    },
]
