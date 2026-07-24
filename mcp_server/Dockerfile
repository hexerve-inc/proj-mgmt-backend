FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire mcp_server package
COPY . /app/mcp_server

# Render injects PORT dynamically; default to 8001 for local testing
ENV PORT=8001
EXPOSE ${PORT}

# Run the server module
CMD ["python", "-m", "mcp_server.server"]
