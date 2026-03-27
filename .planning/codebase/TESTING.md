# Testing Patterns
_Generated: 2026-03-27_

## Summary

No tests exist in this codebase. There is no test framework configured, no test files, no CI pipeline, and no coverage tooling. This document describes the current state and prescribes the patterns to establish when tests are introduced.

---

## Current State

- **Test files:** None found
- **Test framework:** Not configured
- **Coverage tooling:** Not configured
- **CI pipeline:** Not present (no `.github/`, `.circleci/`, `Jenkinsfile`, etc.)
- **Test directories:** None

---

## Recommended Framework

**Runner:** `pytest`

Install:
```bash
pip install pytest pytest-asyncio httpx pytest-cov
```

Add to `requirements.txt` (or a separate `requirements-dev.txt`):
```
pytest
pytest-asyncio
httpx
pytest-cov
```

`httpx` is required for FastAPI's `TestClient` (async-compatible test HTTP client).

---

## Recommended Test File Organization

Place tests in a top-level `tests/` directory, mirroring source structure:

```
tests/
├── __init__.py
├── test_server.py       # Unit/integration tests for server.py
└── conftest.py          # Shared fixtures (app client, sample protobuf messages)
```

**Naming convention:**
- Test files: `test_<module>.py`
- Test functions: `def test_<behaviour_description>():`
- Test classes: `class Test<Subject>:` (use sparingly; prefer flat functions)

---

## Test Structure

**Suite pattern:**
```python
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

@pytest.mark.unit
def test_opamp_handler_returns_protobuf_response():
    ...

@pytest.mark.integration
def test_opamp_handler_decodes_valid_message():
    ...
```

**Fixture pattern (conftest.py):**
```python
import pytest
from fastapi.testclient import TestClient
from server import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def minimal_agent_to_server_bytes():
    import opamp_pb2 as opamp
    msg = opamp.AgentToServer()
    msg.instance_uid = b"test-agent-001"
    return msg.SerializeToString()
```

---

## What to Test

**`server.py` — `opamp_handler`:**

| Scenario | Test type |
|----------|-----------|
| Valid protobuf body returns 200 with protobuf content-type | Integration |
| Valid body deserializes into `ServerToAgent` with `instance_uid` set | Integration |
| Malformed/empty body returns error JSON | Unit |
| Zero-byte body triggers `DecodeError` path | Unit |
| Response `media_type` is `application/x-protobuf` | Integration |

---

## Mocking

**Framework:** `unittest.mock` (stdlib) or `pytest-mock`

**What to mock:**
- External I/O (none currently, but future DB or remote calls)
- `request.body()` when testing error branches in isolation

**What NOT to mock:**
- Protobuf serialization/deserialization — test with real messages
- The FastAPI `TestClient` — use it directly against the real `app`

---

## Running Tests

```bash
pytest                                  # Run all tests
pytest -v                               # Verbose output
pytest --cov=. --cov-report=term-missing  # With coverage
pytest -m unit                          # Unit tests only
pytest -m integration                   # Integration tests only
```

---

## Coverage

**Target:** 80% minimum (per project testing standards)

**View coverage:**
```bash
pytest --cov=. --cov-report=term-missing
```

**Coverage config (add to `pyproject.toml` when created):**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["."]
omit = ["tests/*", "*_pb2.py", "venv/*"]
```

Protobuf-generated files (`opamp_pb2.py`, `anyvalue_pb2.py`) must be excluded from coverage — they are not hand-written code.

---

## Test Types

**Unit Tests:**
- Scope: individual functions in isolation
- Fast, no network/filesystem I/O
- Mark with `@pytest.mark.unit`

**Integration Tests:**
- Scope: full HTTP request/response cycle through FastAPI `TestClient`
- Tests the handler end-to-end with real protobuf encode/decode
- Mark with `@pytest.mark.integration`

**E2E Tests:**
- Not applicable at current scale
- Would require a running collector container; defer until a docker-compose test harness exists

---

## Async Testing

The `opamp_handler` is declared `async`. Use `pytest-asyncio` and FastAPI's synchronous `TestClient` (which handles the event loop internally), or use `httpx.AsyncClient` for fully async tests:

```python
import pytest
import httpx
from server import app

@pytest.mark.asyncio
async def test_handler_async():
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/opamp", content=b"")
    assert response.status_code == 200
```

---

## CI/CD

No CI pipeline exists. When introducing one, the test command to run is:

```bash
pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

---

*Testing analysis: 2026-03-27*
