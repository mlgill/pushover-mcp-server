FROM python:3.12-slim

WORKDIR /app

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install the package
RUN uv pip install --system -e .

# Expose the default port
EXPOSE 8000

# Run the MCP server in SSE mode
CMD ["pushover-mcp", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
