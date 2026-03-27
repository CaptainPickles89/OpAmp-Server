# Technology Stack
_Generated: 2026-03-27_

## Summary

This project is a minimal Python HTTP server implementing the OpAMP (Open Agent Management Protocol) specification. It receives protobuf-encoded messages from OpenTelemetry Collectors over HTTP and responds with a `ServerToAgent` protobuf message. The server runs in a Docker container based on Python 3.11 slim.

## Languages

**Primary:**
- Python 3.11 — all server logic (`server.py`, `opamp_pb2.py`, `anyvalue_pb2.py`)

**Schema/IDL:**
- Protocol Buffers (proto3) — message schemas in `proto/opamp.proto` and `proto/anyvalue.proto`

## Runtime

**Environment:**
- CPython 3.11 (pinned via `FROM python:3.11-slim` in `Dockerfile`)

**Package Manager:**
- pip (no lockfile — `requirements.txt` present, no `pip.lock` or `poetry.lock`)
- Lockfile: absent

## Frameworks

**Core:**
- FastAPI (unpinned) — HTTP request routing; single POST endpoint `/v1/opamp` in `server.py`

**ASGI Server:**
- Uvicorn with `[standard]` extras (unpinned) — serves FastAPI app; entry command `python server.py` runs `uvicorn.run(app, host="0.0.0.0", port=8000)`

**Build/Dev:**
- Docker — containerised runtime via `Dockerfile`

## Key Dependencies

**Critical:**
- `protobuf>=6.0.0` — decodes/encodes OpAMP protobuf messages; generated stubs (`opamp_pb2.py`, `anyvalue_pb2.py`) were compiled against Protobuf Python 6.32.0
- `fastapi` — HTTP framework; handles async request/response lifecycle in `server.py`
- `uvicorn[standard]` — ASGI server; includes WebSocket and HTTP/2 extras via the `[standard]` marker

**Development (non-runtime):**
- `pylance` — listed in `requirements.txt` but is a VS Code language server extension, not a runtime dependency; likely included in error

## Configuration

**Environment:**
- No environment variables are read by the server code at present
- `PYTHONPATH=/app` is set in `Dockerfile` to ensure in-repo modules resolve correctly

**Build:**
- `Dockerfile` at repo root; single-stage build, copies `server.py`, `opamp_pb2.py`, `anyvalue_pb2.py`, `requirements.txt`
- Exposes port `8000`

## Platform Requirements

**Development:**
- Python 3.11+
- pip
- Docker (optional, for containerised run)
- `protoc` with `protobuf` Python plugin required to regenerate `*_pb2.py` stubs from `proto/*.proto`

**Production:**
- Docker container; `python:3.11-slim` base image
- Listening on `0.0.0.0:8000`

---

*Stack analysis: 2026-03-27*
