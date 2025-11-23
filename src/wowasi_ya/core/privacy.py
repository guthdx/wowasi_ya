"""Privacy Layer - PHI/PII detection and user approval gate."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SensitiveDataType(str, Enum):
    """Types of sensitive data that can be detected."""

    PERSON_NAME = "PERSON"
    EMAIL = "EMAIL_ADDRESS"
    PHONE = "PHONE_NUMBER"
    SSN = "US_SSN"
    CREDIT_CARD = "CREDIT_CARD"
    ADDRESS = "ADDRESS"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    MEDICAL_RECORD = "MEDICAL_RECORD_NUMBER"
    TRIBAL_ID = "TRIBAL_ID"
    IP_ADDRESS = "IP_ADDRESS"
    LOCATION = "LOCATION"


class PrivacyFlag(BaseModel):
    """A detected piece of sensitive information."""

    data_type: SensitiveDataType
    text: str = Field(..., description="The detected sensitive text")
    start: int = Field(..., description="Start position in original text")
    end: int = Field(..., description="End position in original text")
    confidence: float = Field(..., ge=0.0, le=1.0)
    context: str = Field(default="", description="Surrounding context for review")


class PrivacyScanResult(BaseModel):
    """Result of scanning text for sensitive data."""

    original_text: str
    flags: list[PrivacyFlag] = Field(default_factory=list)
    sanitized_text: str = Field(default="")
    requires_approval: bool = Field(default=False)
    high_risk_count: int = Field(default=0)
    medium_risk_count: int = Field(default=0)


@dataclass
class PrivacyConfig:
    """Configuration for privacy detection."""

    confidence_threshold: float = 0.7
    high_risk_types: tuple[SensitiveDataType, ...] = (
        SensitiveDataType.SSN,
        SensitiveDataType.MEDICAL_RECORD,
        SensitiveDataType.CREDIT_CARD,
        SensitiveDataType.TRIBAL_ID,
    )
    enabled_detectors: tuple[SensitiveDataType, ...] = tuple(SensitiveDataType)


class PrivacyLayer:
    """Privacy detection and sanitization layer.

    Uses Microsoft Presidio for PII/PHI detection.
    Runs locally - no data sent to external services.
    """

    def __init__(self, config: PrivacyConfig | None = None) -> None:
        """Initialize the privacy layer.

        Args:
            config: Optional privacy configuration.
        """
        self.config = config or PrivacyConfig()
        self._analyzer: Any = None
        self._anonymizer: Any = None

    def _ensure_initialized(self) -> None:
        """Lazily initialize Presidio analyzers."""
        if self._analyzer is None:
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine

                self._analyzer = AnalyzerEngine()
                self._anonymizer = AnonymizerEngine()
            except ImportError:
                # Presidio not installed - use fallback pattern matching
                self._analyzer = None
                self._anonymizer = None

    def scan(self, text: str) -> PrivacyScanResult:
        """Scan text for sensitive data.

        Args:
            text: Text to scan for PII/PHI.

        Returns:
            PrivacyScanResult with detected flags and sanitized version.
        """
        self._ensure_initialized()

        flags: list[PrivacyFlag] = []

        if self._analyzer is not None:
            # Use Presidio for detection
            results = self._analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self.config.confidence_threshold,
            )

            for result in results:
                try:
                    data_type = SensitiveDataType(result.entity_type)
                except ValueError:
                    # Unknown entity type - skip
                    continue

                # Get context (surrounding text)
                context_start = max(0, result.start - 20)
                context_end = min(len(text), result.end + 20)
                context = text[context_start:context_end]

                flags.append(
                    PrivacyFlag(
                        data_type=data_type,
                        text=text[result.start : result.end],
                        start=result.start,
                        end=result.end,
                        confidence=result.score,
                        context=f"...{context}...",
                    )
                )
        else:
            # Fallback: Use basic pattern matching
            flags = self._fallback_scan(text)

        # Calculate risk counts
        high_risk = sum(
            1 for f in flags if f.data_type in self.config.high_risk_types
        )
        medium_risk = len(flags) - high_risk

        # Generate sanitized text
        sanitized = self._sanitize(text, flags)

        return PrivacyScanResult(
            original_text=text,
            flags=flags,
            sanitized_text=sanitized,
            requires_approval=len(flags) > 0,
            high_risk_count=high_risk,
            medium_risk_count=medium_risk,
        )

    def _fallback_scan(self, text: str) -> list[PrivacyFlag]:
        """Basic pattern matching fallback when Presidio is not available."""
        import re

        flags: list[PrivacyFlag] = []

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        for match in re.finditer(email_pattern, text):
            flags.append(
                PrivacyFlag(
                    data_type=SensitiveDataType.EMAIL,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.95,
                    context=text[max(0, match.start() - 20) : match.end() + 20],
                )
            )

        # Phone pattern (US)
        phone_pattern = r"\b(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
        for match in re.finditer(phone_pattern, text):
            flags.append(
                PrivacyFlag(
                    data_type=SensitiveDataType.PHONE,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                    context=text[max(0, match.start() - 20) : match.end() + 20],
                )
            )

        # SSN pattern
        ssn_pattern = r"\b[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{4}\b"
        for match in re.finditer(ssn_pattern, text):
            flags.append(
                PrivacyFlag(
                    data_type=SensitiveDataType.SSN,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.75,
                    context=text[max(0, match.start() - 20) : match.end() + 20],
                )
            )

        return flags

    def _sanitize(self, text: str, flags: list[PrivacyFlag]) -> str:
        """Replace detected sensitive data with placeholders."""
        if not flags:
            return text

        # Sort flags by position (reverse) to replace from end to start
        sorted_flags = sorted(flags, key=lambda f: f.start, reverse=True)

        sanitized = text
        for flag in sorted_flags:
            placeholder = f"[{flag.data_type.value}]"
            sanitized = sanitized[: flag.start] + placeholder + sanitized[flag.end :]

        return sanitized

    def approve(self, scan_result: PrivacyScanResult) -> PrivacyScanResult:
        """Mark a scan result as approved by user.

        Args:
            scan_result: The scan result to approve.

        Returns:
            Updated scan result with approval flag.
        """
        scan_result.requires_approval = False
        return scan_result
