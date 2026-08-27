FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Typically stdio MCP servers don't bind ports, but if run as an SSE server, it would expose a port.
# For stdio, we just run the main script.
CMD ["python", "mcp_server.py"]
