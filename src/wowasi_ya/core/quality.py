"""Quality Checker - Phase 3: Local cross-reference validation + Content Quality.

This module now includes:
1. Structural checks (word count, truncation, empty sections)
2. Content quality checks (generic filler detection, project relevance, specificity)
3. Cross-reference validation
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from wowasi_ya.models.document import Document, GeneratedProject


# Generic filler phrases that indicate low-quality AI output
GENERIC_FILLER_PHRASES = [
    # Vague opening phrases
    "in today's",
    "in this day and age",
    "in the modern world",
    "it is important to note",
    "it should be noted",
    "needless to say",
    "as we all know",
    "as mentioned earlier",
    "in order to",
    "for the purpose of",
    "with respect to",
    "in terms of",
    "at the end of the day",
    "going forward",
    "moving forward",
    "at this point in time",
    "in light of the fact",
    "due to the fact that",
    "on a going forward basis",
    # Generic value statements
    "plays a crucial role",
    "plays an important role",
    "plays a vital role",
    "is essential for success",
    "is key to success",
    "is critical to success",
    "will be important",
    "will be essential",
    "will be crucial",
    "cannot be overstated",
    "is of paramount importance",
    # Filler transitions
    "furthermore",
    "moreover",
    "in addition",
    "additionally",
    "consequently",
    "in conclusion",
    "to summarize",
    "in summary",
    "all in all",
    # AI-specific tells
    "i hope this helps",
    "i'd be happy to",
    "let me know if",
    "feel free to",
    "happy to assist",
    "is designed to",
    "aims to provide",
    "strives to",
    "seeks to address",
]

# Words that indicate AI-generated generic content
AI_VOCABULARY = [
    "delve",
    "tapestry",
    "realm",
    "vibrant",
    "bustling",
    "leverage",
    "utilize",
    "seamlessly",
    "meticulous",
    "intricate",
    "underscore",
    "embark",
    "navigate",
    "landscape",
    "foster",
    "holistic",
    "synergy",
    "paradigm",
    "multifaceted",
    "cutting-edge",
    "best-in-class",
    "state-of-the-art",
    "world-class",
    "robust",
    "scalable",
    "actionable",
    "impactful",
    "transformative",
]


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

        # Check for truncation (CRITICAL - must check first)
        issues.extend(self._check_truncation(doc))

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

        # CONTENT QUALITY CHECKS (the actual quality, not just structure)
        issues.extend(self._check_generic_filler(doc))
        issues.extend(self._check_ai_vocabulary(doc))
        issues.extend(self._check_content_specificity(doc))
        issues.extend(self._check_sentence_variety(doc))

        return issues

    def _check_generic_filler(self, doc: Document) -> list[QualityIssue]:
        """Check for generic filler phrases that indicate low-quality content."""
        issues: list[QualityIssue] = []
        content_lower = doc.content.lower()

        filler_count = 0
        found_fillers = []

        for phrase in GENERIC_FILLER_PHRASES:
            count = content_lower.count(phrase)
            if count > 0:
                filler_count += count
                found_fillers.append(f"'{phrase}' ({count}x)")

        # Calculate filler density (per 1000 words)
        if doc.word_count > 0:
            filler_density = (filler_count / doc.word_count) * 1000

            if filler_density > 20:  # More than 20 filler phrases per 1000 words
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.ERROR,
                        message=f"Excessive generic filler ({filler_count} instances, {filler_density:.1f}/1000 words)",
                        suggestion=f"Remove filler: {', '.join(found_fillers[:5])}",
                    )
                )
            elif filler_density > 10:
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"High filler content ({filler_count} instances, {filler_density:.1f}/1000 words)",
                        suggestion=f"Reduce filler: {', '.join(found_fillers[:3])}",
                    )
                )

        return issues

    def _check_ai_vocabulary(self, doc: Document) -> list[QualityIssue]:
        """Check for AI-typical vocabulary that suggests generic content."""
        issues: list[QualityIssue] = []
        content_lower = doc.content.lower()

        ai_word_count = 0
        found_words = []

        for word in AI_VOCABULARY:
            # Use word boundary matching
            matches = re.findall(rf"\b{re.escape(word)}\b", content_lower)
            if matches:
                ai_word_count += len(matches)
                found_words.append(f"'{word}' ({len(matches)}x)")

        # Calculate AI vocabulary density
        if doc.word_count > 0:
            ai_density = (ai_word_count / doc.word_count) * 1000

            if ai_density > 15:  # More than 15 AI words per 1000 words
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.ERROR,
                        message=f"Heavy AI vocabulary ({ai_word_count} instances, {ai_density:.1f}/1000 words)",
                        suggestion=f"Replace: {', '.join(found_words[:5])}",
                    )
                )
            elif ai_density > 8:
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"Noticeable AI vocabulary ({ai_word_count} instances)",
                        suggestion=f"Consider replacing: {', '.join(found_words[:3])}",
                    )
                )

        return issues

    def _check_content_specificity(self, doc: Document) -> list[QualityIssue]:
        """Check if content is specific vs generic boilerplate.

        Specific content contains:
        - Numbers and metrics
        - Proper nouns (names, places, organizations)
        - Technical terms specific to the domain
        - Dates and deadlines
        """
        issues: list[QualityIssue] = []
        content = doc.content

        # Count specificity indicators
        specificity_score = 0

        # Numbers (budget figures, dates, quantities)
        numbers = re.findall(r"\$[\d,]+|\d+%|\d{4}|\d+(?:,\d{3})+|\d+\s*(?:days?|weeks?|months?|years?|hours?)", content)
        specificity_score += len(numbers) * 2

        # Dates
        dates = re.findall(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?|\d{1,2}/\d{1,2}/\d{2,4}", content)
        specificity_score += len(dates) * 3

        # Capitalized proper nouns (excluding sentence starts)
        lines = content.split("\n")
        proper_nouns = 0
        for line in lines:
            # Find capitalized words not at sentence start
            matches = re.findall(r"(?<=[a-z]\s)[A-Z][a-z]+", line)
            proper_nouns += len(matches)
        specificity_score += proper_nouns

        # Calculate specificity density (per 1000 words)
        if doc.word_count > 0:
            specificity_density = (specificity_score / doc.word_count) * 1000

            if specificity_density < 5:  # Less than 5 specific items per 1000 words
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.ERROR,
                        message=f"Content too generic - lacks specific details (specificity: {specificity_density:.1f}/1000 words)",
                        suggestion="Add specific numbers, dates, names, and concrete details",
                    )
                )
            elif specificity_density < 15:
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"Content could be more specific (specificity: {specificity_density:.1f}/1000 words)",
                        suggestion="Add more concrete details, metrics, and specific references",
                    )
                )

        return issues

    def _check_sentence_variety(self, doc: Document) -> list[QualityIssue]:
        """Check for sentence variety (burstiness).

        Human writing has varied sentence lengths. AI tends to produce uniform lengths.
        """
        issues: list[QualityIssue] = []

        # Extract sentences (simple split by sentence-ending punctuation)
        sentences = re.split(r"[.!?]+", doc.content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]

        if len(sentences) < 5:
            return issues  # Not enough sentences to analyze

        # Calculate word counts per sentence
        lengths = [len(s.split()) for s in sentences]

        # Calculate standard deviation
        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        # Calculate coefficient of variation (CV)
        if mean_length > 0:
            cv = (std_dev / mean_length) * 100

            # Low CV indicates uniform sentence lengths (AI-like)
            if cv < 25:  # Less than 25% variation
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"Low sentence variety (CV: {cv:.1f}%) - sentences too uniform in length",
                        suggestion="Mix short punchy sentences with longer ones for more natural flow",
                    )
                )

        # Check for very long average sentence length
        if mean_length > 30:
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.WARNING,
                    message=f"Average sentence length is {mean_length:.0f} words - may be hard to read",
                    suggestion="Break up long sentences for clarity",
                )
            )

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

    def _check_truncation(self, doc: Document) -> list[QualityIssue]:
        """Check if document appears to be truncated.

        Truncation indicators:
        - Ending mid-sentence (no terminal punctuation)
        - Unbalanced code blocks
        - Unbalanced markdown formatting
        - Document ends with incomplete patterns
        """
        import re

        issues: list[QualityIssue] = []
        content = doc.content.strip()

        if not content:
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.ERROR,
                    message="Document is empty",
                    suggestion="Regenerate this document",
                )
            )
            return issues

        # Check 1: Unbalanced code blocks
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            issues.append(
                QualityIssue(
                    document=doc.filename,
                    severity=IssueSeverity.ERROR,
                    message="Unbalanced code blocks (``` not properly closed) - likely truncated",
                    suggestion="Regenerate this document with higher token limit",
                )
            )

        # Check 2: Ending mid-sentence
        # Get the last substantial line (skip empty lines)
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if lines:
            last_line = lines[-1]

            # Skip if it's a heading, list item closing, code block, or table
            skip_patterns = [
                r"^#+\s",  # Heading
                r"^\|.*\|$",  # Table row
                r"^```",  # Code block marker
                r"^---$",  # Horizontal rule
                r"^\*{3,}$",  # Emphasis rule
            ]
            is_special = any(re.match(p, last_line) for p in skip_patterns)

            if not is_special:
                # Check for terminal punctuation
                valid_endings = (".", "!", "?", ":", ")", "]", '"', "'", "`", "*", "_")
                if not last_line.endswith(valid_endings):
                    # Additional check: is it a list item or table?
                    if not re.match(r"^[-*+]|\d+\.", last_line):
                        issues.append(
                            QualityIssue(
                                document=doc.filename,
                                severity=IssueSeverity.ERROR,
                                message=f"Document ends mid-sentence: '...{last_line[-50:]}'",
                                suggestion="Regenerate this document - it was truncated",
                            )
                        )

        # Check 3: Incomplete markdown patterns
        incomplete_patterns = [
            (r"\*\*[^*]+$", "Unclosed bold text"),
            (r"_[^_]+$", "Unclosed italic text"),
            (r"\[[^\]]*$", "Unclosed link text"),
            (r"\([^)]*$", "Unclosed parenthesis"),
        ]

        for pattern, message in incomplete_patterns:
            if re.search(pattern, content[-200:]):  # Check last 200 chars
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"{message} at end of document - possibly truncated",
                        suggestion="Regenerate this document",
                    )
                )

        # Check 4: Common truncation signals in content
        truncation_signals = [
            "I'll continue",
            "Let me continue",
            "To be continued",
            "...more to follow",
            "[continued]",
        ]
        for signal in truncation_signals:
            if signal.lower() in content.lower()[-500:]:
                issues.append(
                    QualityIssue(
                        document=doc.filename,
                        severity=IssueSeverity.WARNING,
                        message=f"Document contains truncation signal: '{signal}'",
                        suggestion="Regenerate this document with higher token limit",
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

        Uses diminishing returns for warnings to prevent score collapse.
        First few warnings hurt more than many warnings.

        Args:
            issues: List of quality issues.

        Returns:
            Quality score from 0.0 to 1.0.
        """
        if not issues:
            return 1.0

        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in issues if i.severity == IssueSeverity.INFO]

        # Error deduction: each error is significant
        error_deduction = len(errors) * 0.08

        # Warning deduction with diminishing returns
        # First 5 warnings: 0.02 each
        # Next 10 warnings: 0.01 each
        # Beyond 15: 0.005 each
        warning_deduction = 0.0
        for i, _ in enumerate(warnings):
            if i < 5:
                warning_deduction += 0.02
            elif i < 15:
                warning_deduction += 0.01
            else:
                warning_deduction += 0.005

        # Info: minimal impact
        info_deduction = len(infos) * 0.002

        total_deduction = error_deduction + warning_deduction + info_deduction

        # Floor at 15% - always give some credit for having content
        return max(0.15, 1.0 - total_deduction)

    def generate_quality_report(self, project: GeneratedProject) -> str:
        """Generate a human-readable quality report for a project.

        Args:
            project: The generated project to analyze.

        Returns:
            Formatted quality report as a string.
        """
        all_issues = self.check_project(project)
        score = self.get_quality_score(all_issues)

        # Categorize issues
        errors = [i for i in all_issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in all_issues if i.severity == IssueSeverity.WARNING]
        infos = [i for i in all_issues if i.severity == IssueSeverity.INFO]

        # Build report
        lines = [
            "=" * 60,
            "QUALITY REPORT",
            "=" * 60,
            "",
            f"Overall Score: {score:.0%}",
            f"Documents: {len(project.documents)}/15",
            f"Total Words: {sum(d.word_count for d in project.documents):,}",
            "",
            f"Issues: {len(errors)} errors, {len(warnings)} warnings, {len(infos)} info",
            "",
        ]

        # Grade interpretation
        if score >= 0.9:
            lines.append("Grade: A - Excellent quality, ready for use")
        elif score >= 0.75:
            lines.append("Grade: B - Good quality, minor improvements recommended")
        elif score >= 0.6:
            lines.append("Grade: C - Acceptable, but needs attention")
        elif score >= 0.4:
            lines.append("Grade: D - Poor quality, significant issues")
        else:
            lines.append("Grade: F - Failed quality check, regeneration recommended")

        # List errors
        if errors:
            lines.append("")
            lines.append("-" * 40)
            lines.append("ERRORS (must fix):")
            lines.append("-" * 40)
            for issue in errors[:10]:  # Limit to first 10
                lines.append(f"  [{issue.document}]")
                lines.append(f"    {issue.message}")
                if issue.suggestion:
                    lines.append(f"    → {issue.suggestion}")

        # List warnings
        if warnings:
            lines.append("")
            lines.append("-" * 40)
            lines.append("WARNINGS (should fix):")
            lines.append("-" * 40)
            for issue in warnings[:10]:  # Limit to first 10
                lines.append(f"  [{issue.document}]")
                lines.append(f"    {issue.message}")

        # Summary by document
        lines.append("")
        lines.append("-" * 40)
        lines.append("DOCUMENT SUMMARY:")
        lines.append("-" * 40)

        for doc in project.documents:
            doc_issues = [i for i in all_issues if i.document == doc.filename]
            doc_errors = len([i for i in doc_issues if i.severity == IssueSeverity.ERROR])
            doc_warnings = len([i for i in doc_issues if i.severity == IssueSeverity.WARNING])

            status = "✓" if doc_errors == 0 else "✗"
            lines.append(f"  {status} {doc.filename} ({doc.word_count} words, {doc_errors}E/{doc_warnings}W)")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
