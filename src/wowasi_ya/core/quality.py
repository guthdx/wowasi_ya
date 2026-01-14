"""Quality Checker - Phase 3: Local cross-reference validation."""

from dataclasses import dataclass
from enum import Enum

from wowasi_ya.models.document import Document, GeneratedProject


class IssueSeverity(str, Enum):
    """Severity levels for quality issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class QualityIssue:
    """A quality issue found during validation."""

    document: str
    severity: IssueSeverity
    message: str
    line: int | None = None
    suggestion: str | None = None


class QualityChecker:
    """Quality validation for generated documents.

    This is Phase 3 - runs entirely locally.
    Performs cross-reference validation, consistency checks, and completeness verification.
    """

    def __init__(self) -> None:
        """Initialize the quality checker."""
        self.min_word_count = 100
        self.max_word_count = 10000

    def check_document(self, doc: Document) -> list[QualityIssue]:
        """Check a single document for quality issues.

        Args:
            doc: Document to check.

        Returns:
            List of quality issues found.
        """
        issues: list[QualityIssue] = []

        # Check word count
        if doc.word_count < self.min_word_count:
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.WARNING,
                    message=f"Document has only {doc.word_count} words (minimum: {self.min_word_count})",
                    suggestion="Consider expanding the content with more detail",
                )
            )
        elif doc.word_count > self.max_word_count:
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.WARNING,
                    message=f"Document has {doc.word_count} words (maximum: {self.max_word_count})",
                    suggestion="Consider splitting into multiple sections or documents",
                )
            )

        # Check for title
        if not doc.content.strip().startswith("#"):
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.ERROR,
                    message="Document does not start with a title heading",
                    suggestion="Add an H1 heading at the beginning",
                )
            )

        # Check for empty sections
        issues.extend(self._check_empty_sections(doc))

        # Check for placeholder text
        issues.extend(self._check_placeholders(doc))

        return issues

    def _check_empty_sections(self, doc: Document) -> list[QualityIssue]:
        """Check for empty sections in a document."""
        issues: list[QualityIssue] = []
        lines = doc.content.split("\n")

        current_heading = None
        content_after_heading = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("#"):
                if current_heading and not content_after_heading:
                    issues.append(
                        QualityIssue(
                            document=doc.filename,
                            severity=IssueSeverity.WARNING,
                            message=f"Empty section: {current_heading}",
                            line=i,
                            suggestion="Add content or remove the empty section",
                        )
                    )
                current_heading = stripped
                content_after_heading = False
            elif stripped and current_heading:
                content_after_heading = True

        return issues

    def _check_placeholders(self, doc: Document) -> list[QualityIssue]:
        """Check for placeholder text that wasn't replaced."""
        issues: list[QualityIssue] = []
        placeholders = [
            "[TODO]",
            "[PLACEHOLDER]",
            "[INSERT]",
            "[TBD]",
            "Lorem ipsum",
            "XXX",
            "FIXME",
        ]

        lines = doc.content.split("\n")
        for i, line in enumerate(lines):
            for placeholder in placeholders:
                if placeholder.lower() in line.lower():
                    issues.append(
                        QualityIssue(
                            document=doc.filename,
                            severity=IssueSeverity.ERROR,
                            message=f"Placeholder text found: {placeholder}",
                            line=i + 1,
                            suggestion="Replace placeholder with actual content",
                        )
                    )

        return issues

    def check_cross_references(self, project: GeneratedProject) -> list[QualityIssue]:
        """Check cross-references between documents.

        Args:
            project: Complete generated project.

        Returns:
            List of cross-reference issues.
        """
        issues: list[QualityIssue] = []

        # Build glossary terms if available
        glossary_terms = self._extract_glossary_terms(project)

        # Check for undefined terms used in documents
        for doc in project.documents:
            if doc.filename == "Glossary.md":
                continue

            # Look for terms that might need glossary entries
            undefined = self._find_undefined_terms(doc, glossary_terms)
            for term in undefined:
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.INFO,
                        message=f"Term '{term}' might need a glossary entry",
                        suggestion="Consider adding this term to the Glossary",
                    )
                )

        # Check stakeholder consistency
        issues.extend(self._check_stakeholder_consistency(project))

        return issues

    def _extract_glossary_terms(self, project: GeneratedProject) -> set[str]:
        """Extract defined terms from the glossary document."""
        terms: set[str] = set()

        for doc in project.documents:
            if doc.filename == "Glossary.md":
                # Simple extraction: look for **Term** or ## Term patterns
                import re

                bold_terms = re.findall(r"\*\*([^*]+)\*\*", doc.content)
                heading_terms = re.findall(r"^##\s+(.+)$", doc.content, re.MULTILINE)
                terms.update(t.lower() for t in bold_terms + heading_terms)
                break

        return terms

    def _find_undefined_terms(self, doc: Document, glossary_terms: set[str]) -> list[str]:
        """Find potentially undefined technical terms."""
        # This is a simplified check - could be enhanced with NLP
        import re

        # Look for capitalized terms or acronyms that might need definition
        potential_terms = re.findall(r"\b[A-Z]{2,}\b", doc.content)
        acronyms = set(potential_terms)

        # Filter out common acronyms
        common = {"API", "UI", "URL", "HTTP", "HTTPS", "SQL", "PDF", "CSV", "JSON", "XML"}
        undefined = acronyms - common - {t.upper() for t in glossary_terms}

        return list(undefined)[:5]  # Limit to 5 suggestions

    def _check_stakeholder_consistency(self, project: GeneratedProject) -> list[QualityIssue]:
        """Check that stakeholders are consistently referenced."""
        issues: list[QualityIssue] = []

        # Extract stakeholders from Stakeholder-Notes.md
        stakeholders: set[str] = set()
        for doc in project.documents:
            if doc.filename == "Stakeholder-Notes.md":
                # Simple extraction
                import re

                matches = re.findall(r"##\s+(.+)", doc.content)
                stakeholders.update(m.strip().lower() for m in matches)
                break

        # Could add checks for stakeholder references in other documents
        # For now, just verify stakeholder doc exists and has content
        if not stakeholders:
            issues.append(
                QualityIssue(
                    document="Stakeholder-Notes.md",
                    severity=IssueSeverity.WARNING,
                    message="No stakeholders identified in Stakeholder Notes",
                    suggestion="Add stakeholder sections with ## headings",
                )
            )

        return issues

    def check_project(self, project: GeneratedProject) -> list[QualityIssue]:
        """Run all quality checks on a project.

        Args:
            project: Complete generated project.

        Returns:
            List of all quality issues found.
        """
        all_issues: list[QualityIssue] = []

        # Check individual documents
        for doc in project.documents:
            all_issues.extend(self.check_document(doc))

        # Check cross-references
        all_issues.extend(self.check_cross_references(project))

        # Check completeness
        if len(project.documents) < 15:
            all_issues.append(
                QualityIssue(
                    document="(project)",
                    severity=IssueSeverity.ERROR,
                    message=f"Only {len(project.documents)}/15 documents generated",
                    suggestion="Regenerate missing documents",
                )
            )

        return all_issues

    def get_quality_score(self, issues: list[QualityIssue]) -> float:
        """Calculate an overall quality score.

        Args:
            issues: List of quality issues.

        Returns:
            Quality score from 0.0 to 1.0.
        """
        if not issues:
            return 1.0

        # Weight by severity
        error_weight = 0.2
        warning_weight = 0.05
        info_weight = 0.01

        deduction = sum(
            error_weight if i.severity == IssueSeverity.ERROR
            else warning_weight if i.severity == IssueSeverity.WARNING
            else info_weight
            for i in issues
        )

        return max(0.0, 1.0 - deduction)

    def generate_quality_report(self, project: GeneratedProject) -> str:
        """Generate a formatted quality report for display.

        Args:
            project: Complete generated project.

        Returns:
            Formatted string report.
        """
        issues = self.check_project(project)
        score = self.get_quality_score(issues)

        # Build report
        lines = []
        lines.append(f"Documents Generated: {len(project.documents)}/15")
        lines.append(f"Total Word Count: {project.total_word_count:,}")
        lines.append(f"Quality Score: {score:.0%}")
        lines.append("")

        # Group issues by severity
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in issues if i.severity == IssueSeverity.INFO]

        if errors:
            lines.append(f"[red]Errors ({len(errors)}):[/red]")
            for issue in errors[:5]:
                lines.append(f"  • {issue.document}: {issue.message}")
            if len(errors) > 5:
                lines.append(f"  ... and {len(errors) - 5} more")
            lines.append("")

        if warnings:
            lines.append(f"[yellow]Warnings ({len(warnings)}):[/yellow]")
            for issue in warnings[:5]:
                lines.append(f"  • {issue.document}: {issue.message}")
            if len(warnings) > 5:
                lines.append(f"  ... and {len(warnings) - 5} more")
            lines.append("")

        if infos:
            lines.append(f"[blue]Info ({len(infos)}):[/blue]")
            for issue in infos[:3]:
                lines.append(f"  • {issue.document}: {issue.message}")
            if len(infos) > 3:
                lines.append(f"  ... and {len(infos) - 3} more")

        if not issues:
            lines.append("[green]✓ No quality issues found![/green]")

        return "\n".join(lines)
