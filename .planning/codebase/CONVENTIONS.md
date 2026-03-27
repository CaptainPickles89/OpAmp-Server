# Coding Conventions
_Generated: 2026-03-27_

## Summary

This is a minimal Python FastAPI project with a single application file (`server.py`) and two auto-generated protobuf stubs. No linting, formatting, or type-checking tooling is currently configured. The conventions observed are based entirely on the hand-written code in `server.py`.

---

## Naming Patterns

**Files:**
- Snake_case for Python source: `server.py`, `anyvalue_pb2.py`, `opamp_pb2.py`
- Protobuf stubs follow protoc naming convention: `<name>_pb2.py`

**Functions:**
- Snake_case async functions for route handlers: `async def opamp_handler(...)`

**Variables:**
- Snake_case for all local variables: `body`, `msg`, `resp`
- Module-level logger named after the service: `logger = logging.getLogger("opamp-server")`
- FastAPI app instance named `app`

**Constants:**
- No dedicated constants file or `UPPER_SNAKE_CASE` constants defined; hardcoded values are inline (e.g., `b"server-1234"` in `server.py:25`)

---

## Code Style

**Formatting:**
- No formatter configured (no `pyproject.toml`, `.black`, or `ruff.toml` present)
- Existing code is PEP 8-compatible in whitespace and line length
- Blank line between module-level statements (logger setup, app init, route handler)

**Linting:**
- No linter configured (no `.flake8`, `ruff.toml`, or `pyproject.toml`)
- `pylance` is listed in `requirements.txt` — intended as an IDE type checker, not a CI linter

**Recommended tooling to introduce (not yet present):**
- `black` for formatting
- `ruff` for linting
- `mypy` or `pyright` for type checking

---

## Type Annotations

No type annotations are present on function signatures. The single handler in `server.py` has no return type annotation and no parameter type beyond the FastAPI `Request` injection.

Pattern to follow when adding annotations:
```python
async def opamp_handler(request: Request) -> Response:
```

---

## Import Organization

Current order in `server.py`:
1. Standard library (`logging`)
2. Third-party (`fastapi`, `google.protobuf`, `uvicorn`)
3. Local/generated (`opamp_pb2 as opamp`)

No `isort` or explicit grouping enforced yet — follow PEP 8 import ordering manually until tooling is added.

---

## Logging

**Framework:** Python standard library `logging`

**Setup:** Module-level `basicConfig` at `INFO` level in `server.py:7-8`

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opamp-server")
```

**Patterns observed:**
- `logger.info(f"...")` for normal request flow
- `logger.error(f"...")` on caught exceptions
- f-strings used for message interpolation
- No `print()` statements in hand-written code

---

## Error Handling

**Pattern:** `try/except` at the route-handler level catching specific exception types.

```python
except DecodeError as e:
    logger.error(f"Failed to parse Protobuf: {e}")
    return {"error": "invalid protobuf"}
```

**Gaps:**
- Error response returns a plain `dict` (not a `Response` object with a proper HTTP status code)
- No global exception handler registered on the FastAPI `app`
- No input validation beyond protobuf decode failure

---

## Module Design

**Entry point guard:** `if __name__ == "__main__":` present in `server.py` for direct execution via `uvicorn.run()`

**Exports:** No `__init__.py` or package structure — everything is flat at the project root

**Protobuf stubs:** `anyvalue_pb2.py` and `opamp_pb2.py` are generated files. Do not edit them manually; regenerate with `protoc` from `proto/anyvalue.proto` and `proto/opamp.proto`.

---

## Comments

**Inline comments:** Used to label logical steps within the handler (e.g., `# Decode incoming AgentToServer message`, `# Build minimal ServerToAgent response`)

**No docstrings** on any function or module currently.

---

## File Size Guidelines

`server.py` is currently 36 lines. As the server grows, extract:
- Route handlers into a `routes/` package
- Business logic into a `services/` layer
- Configuration into a `config.py` module

---

*Convention analysis: 2026-03-27*
