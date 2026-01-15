# Pushover MCP Server

An MCP (Model Context Protocol) server that enables sending Pushover notifications from Cursor and other MCP-compatible tools.

## Features

- **pushover_send** - Send push notifications with full customization (priority, sound, URL, HTML, TTL)
- **pushover_send_urgent** - Send high-priority notifications with loud sounds
- **pushover_validate** - Validate credentials and list devices
- **pushover_limits** - Check API message limits
- **pushover_health** - Health check for the server

## Prerequisites

1. Create a Pushover account at https://pushover.net
2. Register an application at https://pushover.net/apps to get your **App Token**
3. Get your **User Key** from your Pushover dashboard
4. Install [uv](https://docs.astral.sh/uv/) for Python package management

## Installation in Cursor

Add to your global Cursor MCP configuration at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "Pushover": {
      "command": "/bin/sh",
      "args": ["-c", "cd \"$HOME/code/pushover-mcp-server\" && uv run pushover-mcp"],
      "env": {
        "PUSHOVER_TOKEN": "your-app-token-here",
        "PUSHOVER_USER_KEY": "your-user-key-here"
      }
    }
  }
}
```

This config works on both Linux and macOS by using a shell to expand `$HOME`.

## Installing on Multiple Machines

### Option 1: Clone the repo (recommended)

1. **Clone the repo** to each machine at `~/code/pushover-mcp-server`
2. Ensure `uv` is installed on each machine
3. Add the config to `~/.cursor/mcp.json` on each machine
4. Replace the token and user key values with your actual Pushover credentials
5. Restart Cursor

### Option 2: Install directly from GitHub (no clone needed)

Install the package from GitHub:

```bash
# Via SSH (private repos)
uv pip install git+ssh://git@github.com/mlgill/pushover-mcp-server.git

# Via HTTPS (public repos, or with token for private)
uv pip install git+https://github.com/mlgill/pushover-mcp-server.git

# Specific branch or tag
uv pip install git+ssh://git@github.com/mlgill/pushover-mcp-server.git@main
```

Then use this Cursor config:

```json
{
  "mcpServers": {
    "Pushover": {
      "command": "uvx",
      "args": [
        "--from", "git+ssh://git@github.com/mlgill/pushover-mcp-server.git",
        "pushover-mcp"
      ],
      "env": {
        "PUSHOVER_TOKEN": "your-app-token-here",
        "PUSHOVER_USER_KEY": "your-user-key-here"
      }
    }
  }
}
```

This requires SSH access to the GitHub repo on each machine.

### Option 3: Install from PyPI (after publishing)

If published to PyPI, use the simplest configuration:

```json
{
  "mcpServers": {
    "Pushover": {
      "command": "uvx",
      "args": ["pushover-mcp"],
      "env": {
        "PUSHOVER_TOKEN": "your-app-token-here",
        "PUSHOVER_USER_KEY": "your-user-key-here"
      }
    }
  }
}
```

## Publishing

### Build the package

```bash
uv build
```

### Publish to PyPI

1. Copy `.pypirc.example` to `~/.pypirc` and add your PyPI API token
2. Publish:

```bash
uv publish
```

### Publish to Test PyPI (for testing)

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

## Local Development

```bash
# Install dependencies
uv sync

# Run the server (stdio mode for Cursor)
uv run pushover-mcp

# Run in SSE mode (HTTP server)
uv run pushover-mcp --transport sse --port 8000
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PUSHOVER_TOKEN` | Yes | Your Pushover application API token |
| `PUSHOVER_USER_KEY` | Yes | Your Pushover user or group key |

Alternatively, create a config file at `~/.config/pushover-mcp/config.json`:

```json
{
  "token": "your-app-token",
  "user_key": "your-user-key"
}
```

## Available Tools

### pushover_send

Send a push notification via Pushover with full customization.

**Parameters:**
- `message` (required): Message body (max 1024 characters)
- `title` (optional): Message title (max 250 characters)
- `priority` (optional): -2 (silent), -1 (quiet), 0 (normal), 1 (high), 2 (emergency)
- `sound` (optional): Notification sound (pushover, bike, siren, cosmic, etc.)
- `device` (optional): Target specific device name
- `url` (optional): Supplementary URL
- `url_title` (optional): Title for the URL
- `html` (optional): Enable HTML formatting
- `ttl` (optional): Time to live in seconds (auto-delete)

### pushover_send_urgent

Send a high-priority notification with a loud sound (default: siren).

**Parameters:**
- `message` (required): Urgent message body
- `title` (optional): Message title
- `sound` (optional): Sound to use (default: siren)

### pushover_validate

Validate credentials and list registered devices. No parameters required.

### pushover_limits

Check API message limits (monthly limit, remaining, reset time). No parameters required.

### pushover_health

Health check that validates credentials and confirms the server is working.

## License

MIT
