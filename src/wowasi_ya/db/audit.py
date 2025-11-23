"""Audit logging for API interactions."""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Types of actions that can be audited."""

    PROJECT_CREATED = "project_created"
    PRIVACY_SCANNED = "privacy_scanned"
    PRIVACY_APPROVED = "privacy_approved"
    PRIVACY_DENIED = "privacy_denied"
    API_CALL_RESEARCH = "api_call_research"
    API_CALL_GENERATE = "api_call_generate"
    DOCUMENTS_GENERATED = "documents_generated"
    OUTPUT_WRITTEN = "output_written"
    ERROR = "error"


class AuditLog(BaseModel):
    """A single audit log entry."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: AuditAction
    project_id: str | None = None
    user: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error_message: str | None = None


class AuditLogger:
    """Logger for audit trail.

    Stores audit logs to a local JSON file for compliance.
    In production, this could be extended to use a proper database.
    """

    def __init__(self, log_path: Path | None = None) -> None:
        """Initialize the audit logger.

        Args:
            log_path: Path to the audit log file.
        """
        self.log_path = log_path or Path("./audit_log.jsonl")
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        """Ensure the log file exists."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()

    def log(
        self,
        action: AuditAction,
        project_id: str | None = None,
        user: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """Log an audit event.

        Args:
            action: The action being logged.
            project_id: Associated project ID.
            user: User who performed the action.
            details: Additional details about the action.
            success: Whether the action succeeded.
            error_message: Error message if action failed.

        Returns:
            The created audit log entry.
        """
        entry = AuditLog(
            action=action,
            project_id=project_id,
            user=user,
            details=details or {},
            success=success,
            error_message=error_message,
        )

        # Append to log file (JSONL format)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

        return entry

    def get_logs(
        self,
        project_id: str | None = None,
        action: AuditAction | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Retrieve audit logs with optional filtering.

        Args:
            project_id: Filter by project ID.
            action: Filter by action type.
            since: Only return logs after this time.
            limit: Maximum number of logs to return.

        Returns:
            List of matching audit logs.
        """
        logs: list[AuditLog] = []

        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = AuditLog.model_validate_json(line)

                    # Apply filters
                    if project_id and entry.project_id != project_id:
                        continue
                    if action and entry.action != action:
                        continue
                    if since and entry.timestamp < since:
                        continue

                    logs.append(entry)

                    if len(logs) >= limit:
                        break

                except Exception:
                    # Skip malformed entries
                    continue

        return logs

    def get_api_call_count(
        self,
        since: datetime | None = None,
    ) -> dict[str, int]:
        """Get count of API calls for billing/monitoring.

        Args:
            since: Only count calls after this time.

        Returns:
            Dict with counts by action type.
        """
        counts: dict[str, int] = {
            "research_calls": 0,
            "generation_calls": 0,
            "total_api_calls": 0,
        }

        api_actions = {AuditAction.API_CALL_RESEARCH, AuditAction.API_CALL_GENERATE}

        logs = self.get_logs(since=since, limit=10000)
        for log in logs:
            if log.action in api_actions and log.success:
                counts["total_api_calls"] += 1
                if log.action == AuditAction.API_CALL_RESEARCH:
                    counts["research_calls"] += 1
                elif log.action == AuditAction.API_CALL_GENERATE:
                    counts["generation_calls"] += 1

        return counts


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
