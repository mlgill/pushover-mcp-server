"""FastMCP server for Pushover notifications."""

import sys
from typing import Annotated, Literal, Optional

import click
from mcp.server.fastmcp import FastMCP

from .client import SOUNDS, PushoverClient
from .config import load_config

# Initialize FastMCP server
mcp = FastMCP("Pushover MCP Server")

# Global client instance (initialized on first use)
_client: Optional[PushoverClient] = None


def get_client() -> PushoverClient:
    """Get or create the Pushover client."""
    global _client
    if _client is None:
        config = load_config()
        if not config.is_valid():
            raise ValueError(
                "Pushover credentials not configured. "
                "Set PUSHOVER_TOKEN and PUSHOVER_USER_KEY environment variables, "
                "or create ~/.config/pushover-mcp/config.json"
            )
        _client = PushoverClient(config.token, config.user_key)
    return _client


@mcp.tool()
async def pushover_send(
    message: Annotated[str, "Message body (max 1024 characters)"],
    title: Annotated[Optional[str], "Message title (max 250 characters)"] = None,
    priority: Annotated[int, "Priority: -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)"] = 0,
    sound: Annotated[Optional[str], f"Notification sound: {', '.join(SOUNDS[:10])}..."] = None,
    device: Annotated[Optional[str], "Target specific device name"] = None,
    url: Annotated[Optional[str], "Supplementary URL to include"] = None,
    url_title: Annotated[Optional[str], "Title for the supplementary URL"] = None,
    html: Annotated[bool, "Enable HTML formatting in message"] = False,
    ttl: Annotated[Optional[int], "Time to live in seconds (auto-delete)"] = None,
) -> dict:
    """Send a Pushover notification.
    
    Send a notification to the configured Pushover user/group with full
    customization options including priority levels, sounds, and URLs.
    """
    client = get_client()
    
    # Validate priority
    if priority not in (-2, -1, 0, 1, 2):
        return {"success": False, "error": "Priority must be between -2 and 2"}
    
    response = await client.send_message(
        message=message,
        title=title,
        priority=priority,  # type: ignore
        sound=sound,
        device=device,
        url=url,
        url_title=url_title,
        html=html,
        ttl=ttl,
    )
    
    if response.success:
        return {
            "success": True,
            "message": "Notification sent successfully",
            "request_id": response.request_id,
        }
    else:
        return {
            "success": False,
            "errors": response.errors,
            "request_id": response.request_id,
        }


@mcp.tool()
async def pushover_send_urgent(
    message: Annotated[str, "Urgent message body (max 1024 characters)"],
    title: Annotated[Optional[str], "Message title (max 250 characters)"] = None,
    sound: Annotated[str, "Notification sound (default: siren)"] = "siren",
) -> dict:
    """Send an urgent high-priority Pushover notification.
    
    Sends a priority=1 notification with a loud sound (default: siren).
    Use this when you need immediate attention from the user.
    """
    client = get_client()
    
    response = await client.send_message(
        message=message,
        title=title,
        priority=1,
        sound=sound if sound in SOUNDS else "siren",
    )
    
    if response.success:
        return {
            "success": True,
            "message": "Urgent notification sent successfully",
            "request_id": response.request_id,
        }
    else:
        return {
            "success": False,
            "errors": response.errors,
            "request_id": response.request_id,
        }


@mcp.tool()
async def pushover_validate() -> dict:
    """Validate Pushover credentials and list devices.
    
    Validates the configured user/group key and returns a list of
    registered devices if valid.
    """
    client = get_client()
    
    response = await client.validate_user()
    
    if response.valid:
        return {
            "valid": True,
            "devices": response.devices,
            "licenses": response.licenses,
        }
    else:
        return {
            "valid": False,
            "errors": response.errors,
        }


@mcp.tool()
async def pushover_limits() -> dict:
    """Check Pushover API message limits.
    
    Returns the monthly message limit, remaining messages, and
    when the limit resets (Unix timestamp).
    """
    client = get_client()
    
    response = await client.get_limits()
    
    return {
        "limit": response.limit,
        "remaining": response.remaining,
        "reset_timestamp": response.reset,
        "usage_percent": round((1 - response.remaining / max(response.limit, 1)) * 100, 1),
    }


@mcp.tool()
async def pushover_health() -> dict:
    """Check Pushover MCP server health.
    
    Validates credentials and confirms the server is working correctly.
    """
    try:
        config = load_config()
        if not config.is_valid():
            return {
                "status": "unhealthy",
                "error": "Credentials not configured",
            }
        
        client = get_client()
        response = await client.validate_user()
        
        if response.valid:
            return {
                "status": "healthy",
                "credentials_valid": True,
                "devices": response.devices,
            }
        else:
            return {
                "status": "unhealthy",
                "credentials_valid": False,
                "errors": response.errors,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport mode: stdio (for Cursor) or sse (HTTP server)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (SSE mode only)",
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind to (SSE mode only)",
)
def main(transport: str, host: str, port: int) -> None:
    """Pushover MCP Server - Send notifications via MCP."""
    if transport == "stdio":
        mcp.run()
    else:
        # SSE server mode
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
