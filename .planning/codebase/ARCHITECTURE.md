# Architecture
_Generated: 2026-03-27_

## Summary

This project implements a minimal OpAMP (Open Agent Management Protocol) server in Python using FastAPI. It receives binary Protobuf-encoded messages from OpenTelemetry Collectors over HTTP, decodes them, and returns a stub `ServerToAgent` response. The architecture is a single-file, request-response HTTP server with no persistence, no state management, and no fanout logic — a skeleton implementation of the OpAMP server side.

## Pattern Overview

**Overall:** Single-endpoint HTTP server (synchronous request/response over HTTP POST)

**Key Characteristics:**
- Stateless: no in-memory agent registry, no session tracking, no persistent storage
- Protocol-first: message contract is entirely defined by Protobuf schemas (`opamp.proto`, `anyvalue.proto`)
- Binary wire format: requests and responses use `application/x-protobuf` content type
- Single file server: all server logic is in `server.py` with no module boundaries

## Layers

**HTTP Transport Layer:**
- Purpose: Receive HTTP POST requests from OpAMP agents and return binary protobuf responses
- Location: `server.py` (FastAPI `app` instance, `@app.post("/v1/opamp")` handler)
- Contains: Route definition, request body reading, response serialization
- Depends on: FastAPI, uvicorn, `opamp_pb2`
- Used by: External OpAMP-capable agents (e.g., OpenTelemetry Collector with opamp extension)

**Protocol / Message Layer:**
- Purpose: Encode and decode OpAMP binary messages
- Location: `opamp_pb2.py`, `anyvalue_pb2.py` (generated — do not edit)
- Contains: Protobuf-generated Python classes for all OpAMP message types
- Depends on: `google.protobuf` runtime
- Used by: `server.py`

**Schema / Contract Layer:**
- Purpose: Define the canonical wire format for all OpAMP messages
- Location: `proto/opamp.proto`, `proto/anyvalue.proto`
- Contains: Message definitions, enum types, field annotations
- Depends on: Nothing (source of truth)
- Used by: Protobuf compiler to regenerate `*_pb2.py` stubs

## Data Flow

**Incoming Agent Message (Happy Path):**

1. OpenTelemetry Collector (with opamp extension) sends HTTP POST to `/v1/opamp` with a binary `AgentToServer` protobuf body
2. FastAPI handler in `server.py` reads the raw request body
3. `opamp.AgentToServer().ParseFromString(body)` decodes the binary message
4. Handler logs the decoded message
5. A minimal `opamp.ServerToAgent()` is constructed with a hardcoded `instance_uid = b"server-1234"`
6. Response is serialized via `resp.SerializeToString()` and returned with `Content-Type: application/x-protobuf`

**Error Path:**

1. If `ParseFromString` raises `google.protobuf.message.DecodeError`, handler catches it
2. Logs the error at ERROR level
3. Returns a JSON dict `{"error": "invalid protobuf"}` (note: content type mismatch — response is JSON, not protobuf)

## Key Abstractions

**AgentToServer (incoming):**
- Purpose: Represents a message sent from an OpAMP agent to this server
- Defined in: `proto/opamp.proto` (line 25), generated stub: `opamp_pb2.py`
- Key fields: `instance_uid`, `sequence_num`, `agent_description`, `capabilities`, `health`, `effective_config`, `remote_config_status`, `package_statuses`, `available_components`

**ServerToAgent (outgoing):**
- Purpose: Represents the server's response to an agent
- Defined in: `proto/opamp.proto`, generated stub: `opamp_pb2.py`
- Key fields: `instance_uid`, `error_response`, `remote_config`, `connection_settings`, `flags`, `capabilities`, `agent_identification`, `command`

**AnyValue / KeyValue:**
- Purpose: Generic typed value container used throughout OpAMP for attributes
- Defined in: `proto/anyvalue.proto`, generated stub: `anyvalue_pb2.py`
- Supports: string, bool, int, double, bytes, array, kvlist

## Entry Points

**HTTP Server:**
- Location: `server.py` (line 35: `if __name__ == "__main__": uvicorn.run(...)`)
- Triggers: Direct execution (`python server.py`) or Docker CMD
- Responsibilities: Bind to `0.0.0.0:8000`, serve the FastAPI app

**Docker Entry:**
- Location: `Dockerfile` (line 14: `CMD ["python", "server.py"]`)
- Triggers: Container start
- Responsibilities: Run the server in a Python 3.11-slim container

## Error Handling

**Strategy:** Minimal — only `DecodeError` is explicitly caught. All other exceptions (e.g., network errors, unexpected field types) are unhandled and will surface as 500s via FastAPI's default handler.

**Patterns:**
- `try/except DecodeError` wraps Protobuf parsing in `server.py` (lines 14-33)
- Error response on decode failure returns JSON (not protobuf), which is a protocol inconsistency

## Cross-Cutting Concerns

**Logging:** Python `logging` module at INFO level. Logger name: `opamp-server`. Logs message byte size on receipt and full decoded message content.

**Validation:** None beyond Protobuf parsing. No field-level validation of incoming `AgentToServer` messages.

**Authentication:** None. The `/v1/opamp` endpoint accepts all unauthenticated POST requests.

**State / Session:** None. Each request is fully stateless; no agent registry or session cache exists.

## Companion System: OpenTelemetry Collector

The `collector/` directory contains configuration and a Dockerfile for running an OpenTelemetry Collector as the agent side of the OpAMP protocol pair.

**Collector configuration:** `collector/config.yaml`
- Connects to this server at `http://host.containers.internal:8000/v1/opamp` with a 5-second polling interval
- Enables capabilities: `reports_effective_config`, `reports_health`, `reports_available_components`
- Pipeline: OTLP receivers (gRPC + HTTP) → batch processor → debug exporter

**Collector Dockerfile:** `collector/Dockerfile`
- Base image: `otel/opentelemetry-collector-contrib:latest`
- Exposes: 4317 (OTLP gRPC), 4318 (OTLP HTTP), 8098, 8099

---

*Architecture analysis: 2026-03-27*
