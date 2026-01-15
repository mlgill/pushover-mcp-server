"""Async Pushover API client using httpx."""

from dataclasses import dataclass
from typing import Any, Literal, Optional

import httpx

# Pushover API base URL
PUSHOVER_API_BASE = "https://api.pushover.net/1"

# Valid priority levels
Priority = Literal[-2, -1, 0, 1, 2]

# Available sounds
SOUNDS = [
    "pushover", "bike", "bugle", "cashregister", "classical", "cosmic",
    "falling", "gamelan", "incoming", "intermission", "magic", "mechanical",
    "pianobar", "siren", "spacealarm", "tugboat", "alien", "climb",
    "persistent", "echo", "updown", "vibrate", "none"
]


@dataclass
class PushoverResponse:
    """Response from Pushover API."""
    
    success: bool
    request_id: str
    errors: list[str]
    raw: dict[str, Any]


@dataclass
class ValidationResponse:
    """Response from user validation."""
    
    valid: bool
    devices: list[str]
    licenses: list[str]
    errors: list[str]


@dataclass
class LimitsResponse:
    """Response from limits check."""
    
    limit: int
    remaining: int
    reset: int  # Unix timestamp


class PushoverClient:
    """Async client for Pushover API."""
    
    def __init__(self, token: str, user_key: str):
        self.token = token
        self.user_key = user_key
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def send_message(
        self,
        message: str,
        title: Optional[str] = None,
        priority: Priority = 0,
        sound: Optional[str] = None,
        device: Optional[str] = None,
        url: Optional[str] = None,
        url_title: Optional[str] = None,
        html: bool = False,
        ttl: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> PushoverResponse:
        """Send a notification via Pushover.
        
        Args:
            message: Message body (max 1024 chars)
            title: Message title (max 250 chars)
            priority: -2 (silent) to 2 (emergency)
            sound: Notification sound
            device: Target specific device
            url: Supplementary URL
            url_title: Title for the URL
            html: Enable HTML formatting
            ttl: Time to live in seconds
            timestamp: Unix timestamp for display time
            
        Returns:
            PushoverResponse with success status
        """
        client = await self._get_client()
        
        data = {
            "token": self.token,
            "user": self.user_key,
            "message": message[:1024],  # Enforce limit
        }
        
        if title:
            data["title"] = title[:250]
        if priority != 0:
            data["priority"] = priority
            # Priority 2 requires retry and expire
            if priority == 2:
                data["retry"] = 60  # Retry every 60 seconds
                data["expire"] = 3600  # Expire after 1 hour
        if sound and sound in SOUNDS:
            data["sound"] = sound
        if device:
            data["device"] = device
        if url:
            data["url"] = url[:512]
        if url_title:
            data["url_title"] = url_title[:100]
        if html:
            data["html"] = 1
        if ttl is not None:
            data["ttl"] = ttl
        if timestamp is not None:
            data["timestamp"] = timestamp
        
        response = await client.post(f"{PUSHOVER_API_BASE}/messages.json", data=data)
        result = response.json()
        
        return PushoverResponse(
            success=result.get("status") == 1,
            request_id=result.get("request", ""),
            errors=result.get("errors", []),
            raw=result,
        )
    
    async def validate_user(self, device: Optional[str] = None) -> ValidationResponse:
        """Validate user/group key.
        
        Args:
            device: Optional device name to validate
            
        Returns:
            ValidationResponse with devices list
        """
        client = await self._get_client()
        
        data = {
            "token": self.token,
            "user": self.user_key,
        }
        if device:
            data["device"] = device
        
        response = await client.post(f"{PUSHOVER_API_BASE}/users/validate.json", data=data)
        result = response.json()
        
        return ValidationResponse(
            valid=result.get("status") == 1,
            devices=result.get("devices", []),
            licenses=result.get("licenses", []),
            errors=result.get("errors", []),
        )
    
    async def get_limits(self) -> LimitsResponse:
        """Get application message limits.
        
        Returns:
            LimitsResponse with limit, remaining, and reset timestamp
        """
        client = await self._get_client()
        
        response = await client.get(
            f"{PUSHOVER_API_BASE}/apps/limits.json",
            params={"token": self.token}
        )
        result = response.json()
        
        return LimitsResponse(
            limit=result.get("limit", 0),
            remaining=result.get("remaining", 0),
            reset=result.get("reset", 0),
        )
