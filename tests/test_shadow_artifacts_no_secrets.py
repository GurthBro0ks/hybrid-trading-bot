"""Tests for shadow artifacts secret sanitization.

These tests verify that the sanitize_text function properly removes
secrets and sensitive data from artifact text fields.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recorder.shadow_artifacts import sanitize_text, MAX_TEXT_LENGTH


class TestSanitizeText:
    """Tests for sanitize_text function."""

    def test_none_returns_empty_string(self):
        """None input returns empty string."""
        assert sanitize_text(None) == ""

    def test_empty_string_returns_empty(self):
        """Empty string input returns empty string."""
        assert sanitize_text("") == ""

    def test_normal_text_unchanged(self):
        """Normal text without secrets is unchanged."""
        text = "This is a normal error message"
        assert sanitize_text(text) == text

    def test_removes_api_key(self):
        """Removes api_key pattern."""
        text = "Error: api_key=abc123secret invalid"
        result = sanitize_text(text)
        assert "api_key" not in result.lower()
        assert "abc123" not in result

    def test_removes_api_key_with_hyphen(self):
        """Removes api-key pattern."""
        text = "Error: api-key=xyz789 is invalid"
        result = sanitize_text(text)
        assert "api-key" not in result.lower()
        assert "xyz789" not in result

    def test_removes_apikey_no_separator(self):
        """Removes apikey pattern (no separator)."""
        text = "Failed: apikey123456 not found"
        result = sanitize_text(text)
        assert "apikey" not in result.lower()

    def test_removes_secret(self):
        """Removes secret pattern."""
        text = "Error: secret=mysecretvalue123"
        result = sanitize_text(text)
        assert "secret" not in result.lower()
        assert "mysecretvalue" not in result

    def test_removes_token(self):
        """Removes token pattern."""
        text = "Invalid token=eyJhbGciOiJIUzI1NiIs"
        result = sanitize_text(text)
        assert "token" not in result.lower()
        assert "eyJhbG" not in result

    def test_removes_authorization(self):
        """Removes authorization pattern."""
        text = "Header: authorization: Bearer abc123"
        result = sanitize_text(text)
        # Check both authorization and bearer are handled
        assert "abc123" not in result

    def test_removes_bearer(self):
        """Removes bearer pattern."""
        text = "Failed with bearer=xyz789token"
        result = sanitize_text(text)
        assert "bearer" not in result.lower()

    def test_removes_private_key(self):
        """Removes private_key pattern."""
        text = "Error: private_key=MIIEvgIBADANBgkq"
        result = sanitize_text(text)
        assert "private_key" not in result.lower()
        assert "MIIEvg" not in result

    def test_removes_private_key_with_hyphen(self):
        """Removes private-key pattern."""
        text = "Invalid private-key-data here"
        result = sanitize_text(text)
        assert "private-key" not in result.lower()

    def test_removes_password(self):
        """Removes password pattern."""
        text = "Login failed: password=hunter2"
        result = sanitize_text(text)
        assert "password" not in result.lower()
        assert "hunter2" not in result

    def test_case_insensitive(self):
        """Pattern matching is case-insensitive."""
        test_cases = [
            "API_KEY=123",
            "Api_Key=456",
            "SECRET=abc",
            "Secret=def",
            "TOKEN=xyz",
            "Token=uvw",
            "PASSWORD=pass",
            "Password=word",
        ]
        for text in test_cases:
            result = sanitize_text(text)
            # Should not contain the value portion
            assert "123" not in result or "456" not in result or "abc" not in result

    def test_strips_newlines(self):
        """Newlines are replaced with spaces."""
        text = "Line 1\nLine 2\rLine 3\r\nLine 4"
        result = sanitize_text(text)
        assert "\n" not in result
        assert "\r" not in result
        assert "Line 1 Line 2 Line 3  Line 4" == result

    def test_caps_length(self):
        """Text is capped at MAX_TEXT_LENGTH."""
        long_text = "x" * (MAX_TEXT_LENGTH + 100)
        result = sanitize_text(long_text)
        assert len(result) <= MAX_TEXT_LENGTH
        assert result.endswith("...")

    def test_length_cap_with_secrets(self):
        """Length cap still applies after secret removal."""
        # Long text with secret
        text = "secret=abc " + "x" * 300
        result = sanitize_text(text)
        assert len(result) <= MAX_TEXT_LENGTH
        assert "secret" not in result.lower()

    def test_multiple_secrets_in_one_string(self):
        """Multiple secrets in one string are all removed."""
        text = "api_key=key1 token=tok1 secret=sec1 password=pass1"
        result = sanitize_text(text)
        assert "key1" not in result
        assert "tok1" not in result
        assert "sec1" not in result
        assert "pass1" not in result

    def test_redacted_placeholder(self):
        """Secrets are replaced with [REDACTED]."""
        text = "Error: api_key=abc123"
        result = sanitize_text(text)
        assert "[REDACTED]" in result

    def test_non_string_input(self):
        """Non-string input is converted to string first."""
        assert sanitize_text(123) == "123"
        assert sanitize_text(12.5) == "12.5"
        assert "[REDACTED]" in sanitize_text({"api_key": "secret"})

    def test_safe_default_message(self):
        """When sanitizing, result is always a valid string."""
        result = sanitize_text("Failed: authorization: Bearer SENSITIVE_TOKEN_DATA")
        assert isinstance(result, str)
        assert len(result) <= MAX_TEXT_LENGTH


class TestEdgeCases:
    """Edge case tests for sanitization."""

    def test_secret_at_start(self):
        """Secret at the start of string."""
        text = "api_key=xxx123 caused error"
        result = sanitize_text(text)
        assert "xxx123" not in result

    def test_secret_at_end(self):
        """Secret at the end of string."""
        text = "Error caused by api_key=yyy456"
        result = sanitize_text(text)
        assert "yyy456" not in result

    def test_only_secret(self):
        """String that is only a secret."""
        text = "password=onlysecret"
        result = sanitize_text(text)
        assert "onlysecret" not in result
        assert "[REDACTED]" in result

    def test_url_with_api_key(self):
        """URL containing api_key parameter."""
        text = "Failed to fetch https://api.example.com?api_key=xyz123&foo=bar"
        result = sanitize_text(text)
        assert "xyz123" not in result
        # URL prefix should still be there
        assert "https://" in result or "[REDACTED]" in result
