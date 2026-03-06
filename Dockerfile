# epiminds-swarm API (FastAPI + Gemini)
FROM python:3.12-slim

WORKDIR /app

# Install package and production dependencies (no dev)
COPY pyproject.toml .
COPY src/ src/
COPY README.md .
RUN pip install --no-cache-dir .

# Non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000

# Serve on all interfaces so the container is reachable from outside
CMD ["uvicorn", "swarm.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
