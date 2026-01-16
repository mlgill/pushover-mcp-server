"""Tests for Pushover API client."""

import pytest
from pytest_httpx import HTTPXMock

from pushover_mcp.client import (
    PUSHOVER_API_BASE,
    SOUNDS,
    LimitsResponse,
    PushoverClient,
    PushoverResponse,
    ValidationResponse,
)


class TestPushoverClient:
    """Tests for PushoverClient class."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return PushoverClient(token="test_token", user_key="test_user_key")

    async def test_send_message_success(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Successfully sends a message."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req123"},
        )

        response = await client.send_message("Hello, World!")

        assert response.success is True
        assert response.request_id == "req123"
        assert response.errors == []

    async def test_send_message_with_all_options(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Sends message with all optional parameters."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req456"},
        )

        response = await client.send_message(
            message="Test message",
            title="Test Title",
            priority=1,
            sound="siren",
            device="iphone",
            url="https://example.com",
            url_title="Example",
            html=True,
            ttl=3600,
            timestamp=1234567890,
        )

        assert response.success is True

        # Verify the request was made with correct data
        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "message=Test+message" in body
        assert "title=Test+Title" in body
        assert "priority=1" in body
        assert "sound=siren" in body
        assert "device=iphone" in body
        assert "html=1" in body
        assert "ttl=3600" in body

    async def test_send_message_truncates_long_message(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Message is truncated to 1024 characters."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req789"},
        )

        long_message = "x" * 2000
        await client.send_message(long_message)

        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        # URL-encoded message should be truncated to 1024 chars
        assert "x" * 1024 in body
        assert "x" * 1025 not in body

    async def test_send_message_truncates_long_title(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Title is truncated to 250 characters."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req000"},
        )

        long_title = "t" * 500
        await client.send_message("test", title=long_title)

        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "t" * 250 in body
        assert "t" * 251 not in body

    async def test_send_message_priority_2_adds_retry_expire(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Emergency priority (2) adds retry and expire parameters."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "emergency"},
        )

        await client.send_message("Emergency!", priority=2)

        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "priority=2" in body
        assert "retry=60" in body
        assert "expire=3600" in body

    async def test_send_message_invalid_sound_ignored(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Invalid sound name is not included in request."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req111"},
        )

        await client.send_message("test", sound="invalid_sound_name")

        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "sound=" not in body

    async def test_send_message_failure(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Handles API error response."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 0, "request": "err123", "errors": ["invalid token"]},
        )

        response = await client.send_message("test")

        assert response.success is False
        assert response.request_id == "err123"
        assert response.errors == ["invalid token"]

    async def test_validate_user_success(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Successfully validates user."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/users/validate.json",
            method="POST",
            json={
                "status": 1,
                "devices": ["iphone", "desktop"],
                "licenses": ["iOS"],
            },
        )

        response = await client.validate_user()

        assert response.valid is True
        assert response.devices == ["iphone", "desktop"]
        assert response.licenses == ["iOS"]
        assert response.errors == []

    async def test_validate_user_with_device(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Validates specific device."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/users/validate.json",
            method="POST",
            json={"status": 1, "devices": ["iphone"], "licenses": []},
        )

        await client.validate_user(device="iphone")

        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "device=iphone" in body

    async def test_validate_user_invalid(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Handles invalid user response."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/users/validate.json",
            method="POST",
            json={"status": 0, "errors": ["invalid user key"]},
        )

        response = await client.validate_user()

        assert response.valid is False
        assert response.errors == ["invalid user key"]

    async def test_get_limits(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Gets API limits."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/apps/limits.json?token=test_token",
            method="GET",
            json={"limit": 10000, "remaining": 9500, "reset": 1700000000},
        )

        response = await client.get_limits()

        assert response.limit == 10000
        assert response.remaining == 9500
        assert response.reset == 1700000000

    async def test_client_close(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """Client can be closed properly."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req"},
        )

        # Use the client to create internal httpx client
        await client.send_message("test")
        assert client._client is not None

        # Close should work
        await client.close()
        assert client._client is None

    async def test_client_reuses_http_client(self, client: PushoverClient, httpx_mock: HTTPXMock):
        """HTTP client is reused across calls."""
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req1"},
        )
        httpx_mock.add_response(
            url=f"{PUSHOVER_API_BASE}/messages.json",
            method="POST",
            json={"status": 1, "request": "req2"},
        )

        await client.send_message("first")
        first_client = client._client

        await client.send_message("second")
        second_client = client._client

        assert first_client is second_client


class TestSOUNDS:
    """Tests for the SOUNDS constant."""

    def test_sounds_contains_common_sounds(self):
        """SOUNDS list contains expected values."""
        assert "pushover" in SOUNDS
        assert "siren" in SOUNDS
        assert "none" in SOUNDS

    def test_sounds_is_list(self):
        """SOUNDS is a list."""
        assert isinstance(SOUNDS, list)
        assert len(SOUNDS) > 0


class TestResponseDataclasses:
    """Tests for response dataclasses."""

    def test_pushover_response(self):
        """PushoverResponse stores all fields."""
        response = PushoverResponse(
            success=True,
            request_id="abc123",
            errors=["error1"],
            raw={"status": 1},
        )
        assert response.success is True
        assert response.request_id == "abc123"
        assert response.errors == ["error1"]
        assert response.raw == {"status": 1}

    def test_validation_response(self):
        """ValidationResponse stores all fields."""
        response = ValidationResponse(
            valid=True,
            devices=["phone"],
            licenses=["iOS"],
            errors=[],
        )
        assert response.valid is True
        assert response.devices == ["phone"]
        assert response.licenses == ["iOS"]
        assert response.errors == []

    def test_limits_response(self):
        """LimitsResponse stores all fields."""
        response = LimitsResponse(
            limit=10000,
            remaining=5000,
            reset=1234567890,
        )
        assert response.limit == 10000
        assert response.remaining == 5000
        assert response.reset == 1234567890
