# epiminds-swarm (boilerplate)

Minimal, extendable **swarm agent** architecture in Python, exposed as a **FastAPI** service and powered by **Gemini** via the `google-genai` SDK.

## Requirements

- Python 3.11+ (tested with Python 3.14)

## Setup

Create a virtualenv and install:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

Set environment variables (or use a `.env` file if you run via your own env loader):

```bash
export GEMINI_API_KEY="YOUR_KEY"
export GEMINI_MODEL="gemini-2.0-flash"
```

See [`.env.example`](.env.example) for all supported variables.

## Run the API

```bash
uvicorn swarm.api.main:app --reload --port 8000
```

Health check:

```bash
curl -s http://127.0.0.1:8000/healthz | jq
```

Create a task:

```bash
curl -s http://127.0.0.1:8000/v1/tasks \\
  -H 'content-type: application/json' \\
  -d '{ "input": "Write a haiku about distributed systems.", "max_steps": 4 }' | jq
```

## Notes

- This is intentionally **simple**: in-memory task memory and a rule-based router.\n+- The Gemini client is wrapped so you can swap it out (or fake it in tests) without touching agents/orchestrator.

