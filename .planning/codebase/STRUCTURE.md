# Codebase Structure
_Generated: 2026-03-27_

## Summary

This is a small, flat Python project with no package hierarchy. Server logic lives entirely in `server.py` at the root. Generated Protobuf stubs are co-located at the root alongside the source proto files in `proto/`. The `collector/` directory holds a companion OpenTelemetry Collector configuration used as the agent counterpart during development and testing.

## Directory Layout

```
GitHub-OpAmp-Server/
├── server.py               # FastAPI OpAMP server — sole application entry point
├── opamp_pb2.py            # Generated Protobuf stub for OpAMP messages (DO NOT EDIT)
├── anyvalue_pb2.py         # Generated Protobuf stub for AnyValue types (DO NOT EDIT)
├── requirements.txt        # Python runtime dependencies
├── Dockerfile              # Container image for the OpAMP server
├── README.md               # Minimal project description
├── LICENSE                 # Apache 2.0
├── .gitignore              # Ignores: venv/
├── proto/
│   ├── opamp.proto         # Canonical OpAMP message definitions (source of truth)
│   └── anyvalue.proto      # AnyValue type definitions imported by opamp.proto
└── collector/
    ├── config.yaml         # OTel Collector config with opamp extension pointing at this server
    └── Dockerfile          # Container image for the companion OTel Collector agent
```

## Directory Purposes

**Root (`/`):**
- Purpose: All application source lives here — no src/ or app/ subdirectory
- Contains: Server entry point, generated stubs, dependency manifest, container build files
- Key files: `server.py`, `opamp_pb2.py`, `anyvalue_pb2.py`, `requirements.txt`, `Dockerfile`

**`proto/`:**
- Purpose: Canonical Protobuf schema definitions for the OpAMP protocol
- Contains: `.proto` files only — source of truth for the wire format
- Key files: `proto/opamp.proto`, `proto/anyvalue.proto`
- Note: Changes here require regenerating `opamp_pb2.py` and `anyvalue_pb2.py` using `protoc`

**`collector/`:**
- Purpose: Companion OpenTelemetry Collector configuration used as the agent side of OpAMP
- Contains: Collector YAML config and its Dockerfile
- Key files: `collector/config.yaml`, `collector/Dockerfile`
- Note: Not part of the server application — used for local development/testing of the full agent-server pair

**`.planning/codebase/`:**
- Purpose: GSD planning documents (architecture maps, conventions, etc.)
- Generated: Yes (by GSD tooling)
- Committed: Yes

## Key File Locations

**Entry Points:**
- `server.py`: FastAPI application — defines the `/v1/opamp` HTTP POST handler and starts uvicorn

**Configuration:**
- `requirements.txt`: Python dependencies (`protobuf>=6.0.0`, `fastapi`, `uvicorn[standard]`, `pylance`)
- `Dockerfile`: Builds the server container image from `python:3.11-slim`
- `collector/config.yaml`: OTel Collector pipeline and opamp extension configuration

**Protocol Schemas:**
- `proto/opamp.proto`: All OpAMP message types (`AgentToServer`, `ServerToAgent`, etc.) and enums
- `proto/anyvalue.proto`: `AnyValue`, `KeyValue`, `ArrayValue`, `KeyValueList`

**Generated Code (do not edit):**
- `opamp_pb2.py`: Python Protobuf bindings compiled from `proto/opamp.proto`
- `anyvalue_pb2.py`: Python Protobuf bindings compiled from `proto/anyvalue.proto`

## Naming Conventions

**Files:**
- Application code: `snake_case.py` (e.g., `server.py`)
- Generated Protobuf stubs: `<proto_name>_pb2.py` (e.g., `opamp_pb2.py`) — standard protoc output convention
- Docker: `Dockerfile` (no extension)
- Config: `snake_case.yaml` (e.g., `config.yaml`)

**Directories:**
- Lowercase, short, purpose-named (e.g., `proto/`, `collector/`)

## Where to Add New Code

**New OpAMP message handler logic:**
- Add to `server.py` — create additional handler functions or extend `opamp_handler`
- If `server.py` grows beyond ~200 lines, extract into a `handlers/` package at the root

**New HTTP endpoints:**
- Add `@app.post(...)` / `@app.get(...)` decorators to `server.py`
- For multiple endpoints, consider splitting into a `routers/` directory using FastAPI's `APIRouter`

**Agent state / registry:**
- Create `state.py` or `registry.py` at the root for in-memory agent tracking
- Import into `server.py`

**New Protobuf message types:**
- Edit the relevant `.proto` file in `proto/`
- Regenerate stubs: `python -m grpc_tools.protoc -I proto/ --python_out=. proto/*.proto`
- Commit both the `.proto` source and the regenerated `*_pb2.py` stubs

**Tests:**
- No test directory exists yet
- Create `tests/` at the root
- Use `pytest` with test files named `test_<module>.py` (e.g., `tests/test_server.py`)

**Utilities / shared helpers:**
- Create `utils.py` at the root for small, shared functions
- Use a `utils/` package if helpers are numerous

## Special Directories

**`proto/`:**
- Purpose: Protobuf schema source files
- Generated: No (hand-maintained schema definitions)
- Committed: Yes

**`opamp_pb2.py` / `anyvalue_pb2.py` (root level):**
- Purpose: Generated Python Protobuf bindings
- Generated: Yes (via `protoc` from `proto/*.proto`)
- Committed: Yes (so the container build does not require `protoc` at runtime)

**`venv/` (excluded):**
- Purpose: Local Python virtual environment
- Generated: Yes
- Committed: No (listed in `.gitignore`)

---

*Structure analysis: 2026-03-27*
