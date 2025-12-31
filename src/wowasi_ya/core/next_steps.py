"""Next Steps Engine - Track and manage project action items."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from wowasi_ya.models.document import DocumentType
from wowasi_ya.models.next_steps import (
    ActionType,
    NEXT_STEP_TEMPLATES,
    NextStepTemplate,
    OutlineMapping,
    ProjectNextStep,
    ProjectProgress,
    StepStatus,
)


class NextStepsStore:
    """Persistent storage for project next steps.

    Uses JSONL format for simplicity and consistency with other stores.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize the next steps store.

        Args:
            storage_path: Path to the storage file.
        """
        self.storage_path = storage_path or Path("./next_steps.jsonl")
        self._steps: dict[str, ProjectNextStep] = {}
        self._ensure_storage_file()
        self._load_steps()

    def _ensure_storage_file(self) -> None:
        """Ensure the storage file exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.touch()

    def _load_steps(self) -> None:
        """Load all next steps from disk into memory."""
        if not self.storage_path.exists():
            return

        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    step = ProjectNextStep.model_validate_json(line)
                    self._steps[step.id] = step
                except Exception as e:
                    print(f"Warning: Failed to load next step: {e}")
                    continue

    def _save_all(self) -> None:
        """Write all steps to disk."""
        with self.storage_path.open("w", encoding="utf-8") as f:
            for step in self._steps.values():
                f.write(step.model_dump_json() + "\n")

    def get(self, step_id: str) -> ProjectNextStep | None:
        """Get a next step by ID."""
        return self._steps.get(step_id)

    def get_by_project(self, project_id: str) -> list[ProjectNextStep]:
        """Get all next steps for a project."""
        return [
            step for step in self._steps.values()
            if step.project_id == project_id
        ]

    def get_by_project_and_document(
        self,
        project_id: str,
        document_type: DocumentType,
    ) -> list[ProjectNextStep]:
        """Get next steps for a specific document in a project."""
        return sorted(
            [
                step for step in self._steps.values()
                if step.project_id == project_id and step.document_type == document_type
            ],
            key=lambda s: self._get_template_order(s.template_id),
        )

    def _get_template_order(self, template_id: str) -> int:
        """Get the step order from template ID."""
        for template in NEXT_STEP_TEMPLATES:
            if template["id"] == template_id:
                return template["step_order"]
        return 999

    def save(self, step: ProjectNextStep) -> None:
        """Save or update a next step."""
        step.updated_at = datetime.utcnow()
        self._steps[step.id] = step
        self._save_all()

    def save_many(self, steps: list[ProjectNextStep]) -> None:
        """Save multiple next steps at once."""
        for step in steps:
            step.updated_at = datetime.utcnow()
            self._steps[step.id] = step
        self._save_all()

    def delete(self, step_id: str) -> bool:
        """Delete a next step."""
        if step_id in self._steps:
            del self._steps[step_id]
            self._save_all()
            return True
        return False

    def delete_by_project(self, project_id: str) -> int:
        """Delete all next steps for a project."""
        to_delete = [
            step_id for step_id, step in self._steps.items()
            if step.project_id == project_id
        ]
        for step_id in to_delete:
            del self._steps[step_id]
        if to_delete:
            self._save_all()
        return len(to_delete)


class OutlineMappingStore:
    """Persistent storage for project-to-Outline mappings."""

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize the outline mapping store."""
        self.storage_path = storage_path or Path("./outline_mappings.jsonl")
        self._mappings: dict[str, OutlineMapping] = {}
        self._ensure_storage_file()
        self._load_mappings()

    def _ensure_storage_file(self) -> None:
        """Ensure the storage file exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.touch()

    def _load_mappings(self) -> None:
        """Load all mappings from disk."""
        if not self.storage_path.exists():
            return

        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    mapping = OutlineMapping.model_validate_json(line)
                    self._mappings[mapping.project_id] = mapping
                except Exception as e:
                    print(f"Warning: Failed to load outline mapping: {e}")
                    continue

    def _save_all(self) -> None:
        """Write all mappings to disk."""
        with self.storage_path.open("w", encoding="utf-8") as f:
            for mapping in self._mappings.values():
                f.write(mapping.model_dump_json() + "\n")

    def get_by_project(self, project_id: str) -> OutlineMapping | None:
        """Get mapping for a project."""
        return self._mappings.get(project_id)

    def save(self, mapping: OutlineMapping) -> None:
        """Save or update a mapping."""
        self._mappings[mapping.project_id] = mapping
        self._save_all()

    def delete(self, project_id: str) -> bool:
        """Delete mapping for a project."""
        if project_id in self._mappings:
            del self._mappings[project_id]
            self._save_all()
            return True
        return False


class NextStepsEngine:
    """Engine for managing project next steps.

    Handles:
    - Creating next steps when a project is published
    - Updating step status
    - Calculating progress
    """

    def __init__(
        self,
        steps_store: NextStepsStore | None = None,
        mapping_store: OutlineMappingStore | None = None,
    ) -> None:
        """Initialize the next steps engine."""
        self._steps_store = steps_store or get_steps_store()
        self._mapping_store = mapping_store or get_mapping_store()
        self._templates = self._load_templates()

    def _load_templates(self) -> dict[str, NextStepTemplate]:
        """Load predefined templates into a dict."""
        return {
            t["id"]: NextStepTemplate(**t)
            for t in NEXT_STEP_TEMPLATES
        }

    def get_templates(
        self,
        document_type: DocumentType | None = None,
    ) -> list[NextStepTemplate]:
        """Get all templates, optionally filtered by document type."""
        templates = list(self._templates.values())
        if document_type:
            templates = [t for t in templates if t.document_type == document_type]
        return sorted(templates, key=lambda t: (t.document_type.value, t.step_order))

    def create_steps_for_project(
        self,
        project_id: str,
        document_types: list[DocumentType] | None = None,
    ) -> list[ProjectNextStep]:
        """Create next steps for a project based on templates.

        Args:
            project_id: The project ID.
            document_types: Document types to create steps for.
                           If None, creates steps for all 15 types.

        Returns:
            List of created ProjectNextStep instances.
        """
        if document_types is None:
            document_types = list(DocumentType)

        steps: list[ProjectNextStep] = []
        for template in self._templates.values():
            if template.document_type in document_types:
                step = ProjectNextStep(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    template_id=template.id,
                    document_type=template.document_type,
                    title=template.title,
                    description=template.description,
                    action_type=template.action_type,
                    action_config=template.action_config.copy(),
                    is_required=template.is_required,
                    status=StepStatus.NOT_STARTED,
                )
                steps.append(step)

        # Save all at once
        self._steps_store.save_many(steps)
        return steps

    def get_steps(
        self,
        project_id: str,
        document_type: DocumentType | None = None,
    ) -> list[ProjectNextStep]:
        """Get next steps for a project."""
        if document_type:
            return self._steps_store.get_by_project_and_document(
                project_id, document_type
            )
        return sorted(
            self._steps_store.get_by_project(project_id),
            key=lambda s: (s.document_type.value, self._get_template_order(s.template_id)),
        )

    def _get_template_order(self, template_id: str) -> int:
        """Get step order from template."""
        template = self._templates.get(template_id)
        return template.step_order if template else 999

    def get_step(self, step_id: str) -> ProjectNextStep | None:
        """Get a specific step by ID."""
        return self._steps_store.get(step_id)

    def update_step(
        self,
        step_id: str,
        status: StepStatus | None = None,
        notes: str | None = None,
        output_data: dict[str, Any] | None = None,
        completed_by: str | None = None,
    ) -> ProjectNextStep | None:
        """Update a step's status and data.

        Args:
            step_id: The step ID.
            status: New status (optional).
            notes: Notes to add (optional).
            output_data: Form/checklist data (optional).
            completed_by: Who completed the step (optional).

        Returns:
            Updated step, or None if not found.
        """
        step = self._steps_store.get(step_id)
        if not step:
            return None

        if status is not None:
            step.status = status
            if status == StepStatus.COMPLETED:
                step.completed_at = datetime.utcnow()
                if completed_by:
                    step.completed_by = completed_by

        if notes is not None:
            step.notes = notes

        if output_data is not None:
            step.output_data = output_data

        self._steps_store.save(step)
        return step

    def complete_step(
        self,
        step_id: str,
        completed_by: str | None = None,
        output_data: dict[str, Any] | None = None,
    ) -> ProjectNextStep | None:
        """Mark a step as completed."""
        return self.update_step(
            step_id,
            status=StepStatus.COMPLETED,
            completed_by=completed_by,
            output_data=output_data,
        )

    def skip_step(
        self,
        step_id: str,
        reason: str | None = None,
    ) -> ProjectNextStep | None:
        """Mark a step as skipped."""
        return self.update_step(
            step_id,
            status=StepStatus.SKIPPED,
            notes=f"Skipped: {reason}" if reason else "Skipped by user",
        )

    def get_progress(self, project_id: str) -> ProjectProgress:
        """Calculate progress for a project."""
        steps = self._steps_store.get_by_project(project_id)

        total = len(steps)
        completed = sum(1 for s in steps if s.status == StepStatus.COMPLETED)
        in_progress = sum(1 for s in steps if s.status == StepStatus.IN_PROGRESS)
        skipped = sum(1 for s in steps if s.status == StepStatus.SKIPPED)
        not_started = sum(1 for s in steps if s.status == StepStatus.NOT_STARTED)

        required_total = sum(1 for s in steps if s.is_required)
        required_completed = sum(
            1 for s in steps
            if s.is_required and s.status == StepStatus.COMPLETED
        )

        # Calculate percentage (counting completed and skipped as "done")
        done = completed + skipped
        percentage = (done / total * 100) if total > 0 else 0

        # Progress by document type
        by_doc_type: dict[str, dict[str, int]] = {}
        for doc_type in DocumentType:
            doc_steps = [s for s in steps if s.document_type == doc_type]
            if doc_steps:
                by_doc_type[doc_type.value] = {
                    "total": len(doc_steps),
                    "completed": sum(1 for s in doc_steps if s.status == StepStatus.COMPLETED),
                    "in_progress": sum(1 for s in doc_steps if s.status == StepStatus.IN_PROGRESS),
                    "skipped": sum(1 for s in doc_steps if s.status == StepStatus.SKIPPED),
                    "not_started": sum(1 for s in doc_steps if s.status == StepStatus.NOT_STARTED),
                }

        return ProjectProgress(
            project_id=project_id,
            total_steps=total,
            completed_steps=completed,
            in_progress_steps=in_progress,
            skipped_steps=skipped,
            not_started_steps=not_started,
            completion_percentage=round(percentage, 1),
            required_steps_total=required_total,
            required_steps_completed=required_completed,
            by_document_type=by_doc_type,
        )

    def save_outline_mapping(
        self,
        project_id: str,
        collection_id: str,
        collection_url: str,
        document_ids: dict[str, str],
    ) -> OutlineMapping:
        """Save mapping between project and Outline collection."""
        mapping = OutlineMapping(
            id=str(uuid.uuid4()),
            project_id=project_id,
            outline_collection_id=collection_id,
            outline_collection_url=collection_url,
            outline_document_ids=document_ids,
        )
        self._mapping_store.save(mapping)
        return mapping

    def get_outline_mapping(self, project_id: str) -> OutlineMapping | None:
        """Get Outline mapping for a project."""
        return self._mapping_store.get_by_project(project_id)


# Global instances
_steps_store: NextStepsStore | None = None
_mapping_store: OutlineMappingStore | None = None
_engine: NextStepsEngine | None = None


def get_steps_store() -> NextStepsStore:
    """Get the global next steps store instance."""
    global _steps_store
    if _steps_store is None:
        _steps_store = NextStepsStore()
    return _steps_store


def get_mapping_store() -> OutlineMappingStore:
    """Get the global outline mapping store instance."""
    global _mapping_store
    if _mapping_store is None:
        _mapping_store = OutlineMappingStore()
    return _mapping_store


def get_next_steps_engine() -> NextStepsEngine:
    """Get the global next steps engine instance."""
    global _engine
    if _engine is None:
        _engine = NextStepsEngine()
    return _engine
