"""Persistent storage for project states."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from wowasi_ya.models.project import ProjectState


class ProjectStateStore:
    """Persistent storage for project states.

    Stores project states in a JSONL file (one JSON object per line).
    Loads all states into memory on startup for fast access.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize the project state store.

        Args:
            storage_path: Path to the state storage file.
        """
        self.storage_path = storage_path or Path("./project_states.jsonl")
        self._states: Dict[str, ProjectState] = {}
        self._ensure_storage_file()
        self._load_states()

    def _ensure_storage_file(self) -> None:
        """Ensure the storage file exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.touch()

    def _load_states(self) -> None:
        """Load all project states from disk into memory."""
        if not self.storage_path.exists():
            return

        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    state = ProjectState.model_validate_json(line)
                    self._states[state.id] = state
                except Exception as e:
                    # Log and skip malformed entries
                    print(f"Warning: Failed to load project state: {e}")
                    continue

    def _save_all(self) -> None:
        """Write all states to disk."""
        with self.storage_path.open("w", encoding="utf-8") as f:
            for state in self._states.values():
                f.write(state.model_dump_json() + "\n")

    def get(self, project_id: str) -> ProjectState | None:
        """Get a project state by ID.

        Args:
            project_id: The project ID to retrieve.

        Returns:
            The project state, or None if not found.
        """
        return self._states.get(project_id)

    def set(self, state: ProjectState) -> None:
        """Save or update a project state.

        Args:
            state: The project state to save.
        """
        state.updated_at = datetime.utcnow()
        self._states[state.id] = state
        self._save_all()

    def list_all(self) -> list[ProjectState]:
        """List all project states.

        Returns:
            List of all project states, sorted by creation time (newest first).
        """
        return sorted(
            self._states.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )

    def delete(self, project_id: str) -> bool:
        """Delete a project state.

        Args:
            project_id: The project ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        if project_id in self._states:
            del self._states[project_id]
            self._save_all()
            return True
        return False

    def __len__(self) -> int:
        """Return the number of stored project states."""
        return len(self._states)


# Global project state store instance
_state_store: ProjectStateStore | None = None


def get_state_store() -> ProjectStateStore:
    """Get the global project state store instance."""
    global _state_store
    if _state_store is None:
        _state_store = ProjectStateStore()
    return _state_store
