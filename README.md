# Pushover MCP Server

An MCP (Model Context Protocol) server that enables sending Pushover notifications from Cursor, Claude Code, and other MCP-compatible tools.

## Warning

This repository is a personal project, is not well tested, and is not supported. The code is tested to the extent that I have used it. Others are welcome to fork and use at their own risk.

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

## Installation in Claude Code

Claude Code supports MCP servers at both project and user levels.

### Project-level (recommended for team projects)

Add to `.mcp.json` in your project root:

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

### User-level (available in all projects)

Add to `~/.claude.json`:

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

### One-liner installation

Alternatively, install directly from the command line:

```bash
claude mcp add-json pushover '{
  "command": "uvx",
  "args": [
    "--from",
    "git+ssh://git@github.com/mlgill/pushover-mcp-server.git",
    "pushover-mcp"
  ],
  "env": {
    "PUSHOVER_TOKEN": "xxx",
    "PUSHOVER_USER_KEY": "xxx"
  }
}'
```

Replace `xxx` with your actual Pushover credentials.

After adding the configuration, restart Claude Code or run `/mcp` to reload MCP servers.

### Using with CLAUDE.md

Copy `claude/CLAUDE.md` to your project root to enable automatic notification behavior when Claude Code is waiting for user approval. This configures:

- **2 min idle**: Send normal priority notification
- **8 min idle**: Escalate to high priority (prevents session timeout)

## Installing on Multiple Machines

### Option 1: Clone the repo

1. **Clone the repo** to each machine at `~/code/pushover-mcp-server`
2. Ensure `uv` is installed on each machine
3. Add the config to `~/.cursor/mcp.json` (Cursor) or `~/.claude.json` (Claude Code)
4. Replace the token and user key values with your actual Pushover credentials
5. Restart Cursor or Claude Code

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

Then use this MCP config (in `~/.cursor/mcp.json` or `~/.claude.json`):

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

# Run the server (stdio mode for Cursor/Claude Code)
uv run pushover-mcp
```

## Testing

Run the test suite with pytest:

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_client.py

# Run with coverage (if pytest-cov is installed)
uv run pytest --cov=pushover_mcp
```

## Web Service Deployment

The server can be deployed as a web service using SSE (Server-Sent Events) transport, allowing MCP clients to connect over HTTP.

### Running as a Web Service

```bash
# Run directly with custom host/port
pushover-mcp --transport sse --host 0.0.0.0 --port 8000

# Or with uv
uv run pushover-mcp --transport sse --host 0.0.0.0 --port 8000
```

### Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t pushover-mcp .

# Run the container
docker run -d \
  -p 8000:8000 \
  -e PUSHOVER_TOKEN=your-app-token \
  -e PUSHOVER_USER_KEY=your-user-key \
  --name pushover-mcp \
  pushover-mcp
```

### Docker Compose

For easier deployment, use Docker Compose:

1. Create a `.env` file with your credentials:

```bash
PUSHOVER_TOKEN=your-app-token
PUSHOVER_USER_KEY=your-user-key
```

2. Start the service:

```bash
docker compose up -d
```

The server will be available at `http://localhost:8000`.

### Connecting MCP Clients

Once running as a web service, MCP clients can connect using the SSE endpoint:

```
http://your-server:8000/sse
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
