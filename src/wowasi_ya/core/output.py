"""Output Manager - Write generated documents to various destinations."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from wowasi_ya.config import Settings, get_settings
from wowasi_ya.models.document import GeneratedProject


class OutputWriter(ABC):
    """Abstract base class for output writers."""

    @abstractmethod
    async def write(self, project: GeneratedProject, destination: Path) -> list[str]:
        """Write project documents to destination.

        Args:
            project: Generated project with documents.
            destination: Output destination path.

        Returns:
            List of paths/URLs where documents were written.
        """
        pass


class FilesystemWriter(OutputWriter):
    """Write documents to the local filesystem."""

    async def write(self, project: GeneratedProject, destination: Path) -> list[str]:
        """Write documents to filesystem maintaining folder structure."""
        paths: list[str] = []

        # Create project directory
        project_dir = destination / self._sanitize_name(project.project_name)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create folder structure
        folders = {"00-Overview", "10-Discovery", "20-Planning", "30-Execution", "40-Comms", "90-Archive"}
        for folder in folders:
            (project_dir / folder).mkdir(exist_ok=True)

        # Write each document
        for doc in project.documents:
            doc_path = project_dir / doc.folder / doc.filename
            doc_path.write_text(doc.content, encoding="utf-8")
            paths.append(str(doc_path))

        return paths

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem use."""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")
        return sanitized.strip()


class ObsidianWriter(OutputWriter):
    """Write documents to an Obsidian vault."""

    def __init__(self, vault_path: Path) -> None:
        """Initialize with Obsidian vault path.

        Args:
            vault_path: Path to Obsidian vault root.
        """
        self.vault_path = vault_path

    async def write(self, project: GeneratedProject, destination: Path) -> list[str]:
        """Write documents to Obsidian vault with wiki-style links."""
        paths: list[str] = []

        # Use vault path as destination
        project_dir = self.vault_path / self._sanitize_name(project.project_name)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create folder structure
        folders = {"00-Overview", "10-Discovery", "20-Planning", "30-Execution", "40-Comms", "90-Archive"}
        for folder in folders:
            (project_dir / folder).mkdir(exist_ok=True)

        # Write each document with Obsidian frontmatter
        for doc in project.documents:
            content = self._add_frontmatter(doc.content, doc.title, project.project_name)
            content = self._convert_links(content, project)

            doc_path = project_dir / doc.folder / doc.filename
            doc_path.write_text(content, encoding="utf-8")
            paths.append(str(doc_path))

        return paths

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem use."""
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, "_")
        return sanitized.strip()

    def _add_frontmatter(self, content: str, title: str, project: str) -> str:
        """Add YAML frontmatter for Obsidian."""
        frontmatter = f"""---
title: {title}
project: {project}
created: {datetime.utcnow().isoformat()}
tags:
  - wowasi_ya
  - generated
---

"""
        return frontmatter + content

    def _convert_links(self, content: str, project: GeneratedProject) -> str:
        """Convert markdown links to Obsidian wiki-style links."""
        import re

        # Convert [text](file.md) to [[file|text]]
        def replace_link(match: re.Match[str]) -> str:
            text = match.group(1)
            file = match.group(2)
            if file.endswith(".md"):
                file = file[:-3]  # Remove .md extension
            return f"[[{file}|{text}]]"

        return re.sub(r"\[([^\]]+)\]\(([^)]+\.md)\)", replace_link, content)


class GitWriter(OutputWriter):
    """Write documents to a Git repository."""

    def __init__(self, repo_path: Path, auto_commit: bool = True) -> None:
        """Initialize with Git repository path.

        Args:
            repo_path: Path to Git repository.
            auto_commit: Whether to automatically commit changes.
        """
        self.repo_path = repo_path
        self.auto_commit = auto_commit

    async def write(self, project: GeneratedProject, destination: Path) -> list[str]:
        """Write documents to Git repository and optionally commit."""
        paths: list[str] = []

        # Use filesystem writer for actual file creation
        fs_writer = FilesystemWriter()
        paths = await fs_writer.write(project, self.repo_path)

        if self.auto_commit and paths:
            self._git_commit(project.project_name, len(project.documents))

        return paths

    def _git_commit(self, project_name: str, doc_count: int) -> None:
        """Create a Git commit for the generated documents."""
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Commit
            commit_msg = f"Generated {doc_count} documents for: {project_name}\n\nGenerated by Wowasi_ya"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Git operations failed - continue without commit
            pass


class OutputManager:
    """Manager for writing generated projects to various outputs."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the output manager.

        Args:
            settings: Application settings.
        """
        self.settings = settings or get_settings()

    async def write(
        self,
        project: GeneratedProject,
        output_format: str = "filesystem",
    ) -> list[str]:
        """Write project to the configured output destination.

        Args:
            project: Generated project to write.
            output_format: Output format (filesystem, obsidian, git).

        Returns:
            List of output paths.
        """
        writer: OutputWriter

        if output_format == "obsidian" and self.settings.obsidian_vault_path:
            writer = ObsidianWriter(self.settings.obsidian_vault_path)
            destination = self.settings.obsidian_vault_path
        elif output_format == "git" and self.settings.git_output_path:
            writer = GitWriter(self.settings.git_output_path)
            destination = self.settings.git_output_path
        else:
            writer = FilesystemWriter()
            destination = self.settings.output_dir

        # Ensure output directory exists
        destination.mkdir(parents=True, exist_ok=True)

        return await writer.write(project, destination)

    async def write_all(
        self,
        project: GeneratedProject,
        formats: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """Write project to multiple output destinations.

        Args:
            project: Generated project.
            formats: List of formats to write to.

        Returns:
            Dict mapping format to list of output paths.
        """
        formats = formats or ["filesystem"]
        results: dict[str, list[str]] = {}

        for fmt in formats:
            try:
                paths = await self.write(project, fmt)
                results[fmt] = paths
            except Exception as e:
                results[fmt] = [f"Error: {e!s}"]

        return results
