"""Tests for the privacy layer."""

import pytest

from wowasi_ya.core.privacy import PrivacyLayer, SensitiveDataType


class TestPrivacyLayer:
    """Tests for PrivacyLayer."""

    def test_detects_email_address(self) -> None:
        """Test that email addresses are detected."""
        privacy = PrivacyLayer()
        result = privacy.scan("Contact us at john.doe@example.com for more info.")

        assert result.requires_approval
        assert len(result.flags) >= 1

        email_flags = [f for f in result.flags if f.data_type == SensitiveDataType.EMAIL]
        assert len(email_flags) >= 1
        assert "john.doe@example.com" in email_flags[0].text

    def test_detects_phone_number(self) -> None:
        """Test that phone numbers are detected."""
        privacy = PrivacyLayer()
        result = privacy.scan("Call us at (555) 123-4567 today!")

        assert result.requires_approval
        phone_flags = [f for f in result.flags if f.data_type == SensitiveDataType.PHONE]
        assert len(phone_flags) >= 1

    def test_detects_ssn(self) -> None:
        """Test that SSN patterns are detected."""
        privacy = PrivacyLayer()
        result = privacy.scan("SSN: 123-45-6789")

        assert result.requires_approval
        ssn_flags = [f for f in result.flags if f.data_type == SensitiveDataType.SSN]
        assert len(ssn_flags) >= 1

    def test_no_flags_for_clean_text(self) -> None:
        """Test that clean text has no privacy flags."""
        privacy = PrivacyLayer()
        result = privacy.scan("This is a completely clean description of a project.")

        assert not result.requires_approval
        assert len(result.flags) == 0

    def test_sanitizes_sensitive_data(self) -> None:
        """Test that sensitive data is sanitized in output."""
        privacy = PrivacyLayer()
        result = privacy.scan("Contact john.doe@example.com or call 555-123-4567")

        assert "[EMAIL_ADDRESS]" in result.sanitized_text or "[PHONE_NUMBER]" in result.sanitized_text
        assert "john.doe@example.com" not in result.sanitized_text

    def test_counts_risk_levels(self) -> None:
        """Test that risk levels are properly counted."""
        privacy = PrivacyLayer()
        # SSN is high risk, email is medium risk
        result = privacy.scan("SSN: 123-45-6789, email: test@test.com")

        assert result.high_risk_count >= 1 or result.medium_risk_count >= 1

    def test_provides_context_for_review(self) -> None:
        """Test that context is provided for each flag."""
        privacy = PrivacyLayer()
        result = privacy.scan("Please contact john.doe@example.com for details.")

        for flag in result.flags:
            assert len(flag.context) > 0
            # Context should include surrounding text
            assert "..." in flag.context or flag.text in flag.context

    def test_approve_clears_approval_requirement(self) -> None:
        """Test that approving a scan result clears the flag."""
        privacy = PrivacyLayer()
        result = privacy.scan("Contact: john.doe@example.com")

        assert result.requires_approval
        approved = privacy.approve(result)
        assert not approved.requires_approval


class TestPrivacyLayerMultipleItems:
    """Tests for detecting multiple sensitive items."""

    def test_detects_multiple_emails(self) -> None:
        """Test detection of multiple email addresses."""
        privacy = PrivacyLayer()
        result = privacy.scan(
            "Contact alice@example.com or bob@example.org for assistance."
        )

        email_flags = [f for f in result.flags if f.data_type == SensitiveDataType.EMAIL]
        assert len(email_flags) >= 2

    def test_detects_mixed_sensitive_data(self) -> None:
        """Test detection of multiple types of sensitive data."""
        privacy = PrivacyLayer()
        result = privacy.scan(
            "Name: John Doe, Email: john@test.com, Phone: 555-123-4567"
        )

        types_found = {f.data_type for f in result.flags}
        assert len(types_found) >= 2
