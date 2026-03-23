"""Tests for webhook API key authentication."""

from unittest.mock import patch, MagicMock

from utils.auth import check_api_key, PUBLIC_ENDPOINTS


class TestCheckApiKey:
    def test_auth_disabled_when_no_key_set(self):
        """When WEBHOOK_API_KEY is empty, all requests pass."""
        with patch("utils.auth.WEBHOOK_API_KEY", ""):
            headers = MagicMock()
            assert check_api_key(headers) is True

    def test_bearer_token_valid(self):
        with patch("utils.auth.WEBHOOK_API_KEY", "my-secret-key"):
            headers = MagicMock()
            headers.get = lambda key, default="": {
                "Authorization": "Bearer my-secret-key",
                "X-API-Key": "",
            }.get(key, default)
            assert check_api_key(headers) is True

    def test_x_api_key_valid(self):
        with patch("utils.auth.WEBHOOK_API_KEY", "my-secret-key"):
            headers = MagicMock()
            headers.get = lambda key, default="": {
                "Authorization": "",
                "X-API-Key": "my-secret-key",
            }.get(key, default)
            assert check_api_key(headers) is True

    def test_wrong_key_rejected(self):
        with patch("utils.auth.WEBHOOK_API_KEY", "correct-key"):
            headers = MagicMock()
            headers.get = lambda key, default="": {
                "Authorization": "Bearer wrong-key",
                "X-API-Key": "",
            }.get(key, default)
            assert check_api_key(headers) is False

    def test_no_key_provided_rejected(self):
        with patch("utils.auth.WEBHOOK_API_KEY", "some-key"):
            headers = MagicMock()
            headers.get = lambda key, default="": default
            assert check_api_key(headers) is False

    def test_health_is_public(self):
        assert "/health" in PUBLIC_ENDPOINTS
