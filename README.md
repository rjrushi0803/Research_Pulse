# Research Pulse

A modular, production-oriented research-paper discovery and retrieval-augmented generation (RAG) application.

## Phase 1 scope

- FastAPI application factory and health endpoint
- Environment-based settings
- Pytest API tests
- Ruff linting/formatting
- GitHub Actions continuous integration

Paper providers, databases, embeddings, scheduling, email and chat are intentionally not implemented yet. They will be added in later phases.

## Requirements

- Python 3.13+
- `uv`

Install `uv` using the official instructions for your operating system, then run:

```bash
uv sync --extra dev
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Open:
- Health check: <http://127.0.0.1:8000/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

Expected health response:

```json
{"status":"ok","app_name":"Research RAG","environment":"development"}
```

## Run tests and code checks

```bash
uv run pytest
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
```

To automatically format files during development:

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Configuration

Settings are read from environment variables and, for local development, an optional `.env` file. `.env` is ignored by Git. Do not store API keys or production credentials in source control.

## Public deployment warning

The initial health endpoint is deliberately small and exposes no secrets. **Do not expose the development server directly to the public internet.** Before public use, deploy behind a maintained reverse proxy with HTTPS, firewall rules, restricted administrative access, authentication/authorization for user data, request limits, and production secret management. The `HOST` default is `127.0.0.1` intentionally.

## Project layout

```text
app/
  api/routes/health.py   # HTTP route
  core/config.py         # Central application settings
  main.py                # FastAPI app factory and ASGI entry point
tests/
  test_health.py         # API behavior tests
.github/workflows/ci.yml # Automated checks
```