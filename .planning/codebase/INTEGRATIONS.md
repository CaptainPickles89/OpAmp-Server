# External Integrations
_Generated: 2026-03-27_

## Summary

This server implements the OpAMP (Open Agent Management Protocol) HTTP transport, acting as a management server for OpenTelemetry Collectors. Its only external integration point is inbound HTTP requests from OpAMP-enabled collectors. There are no outbound API calls, databases, message queues, or third-party SaaS integrations.

## APIs & External Services

**OpAMP Protocol (inbound):**
- Spec: [OpenTelemetry OpAMP specification](https://opentelemetry.io/docs/specs/opamp/)
- Transport: HTTP POST to `/v1/opamp`
- Encoding: `application/x-protobuf` (binary protobuf, not JSON)
- Message types:
  - Inbound: `AgentToServer` (defined in `proto/opamp.proto`, generated stub at `opamp_pb2.py`)
  - Outbound: `ServerToAgent` (defined in `proto/opamp.proto`, generated stub at `opamp_pb2.py`)
- Proto dependency: `anyvalue.proto` → `anyvalue_pb2.py` (KeyValue/AnyValue types shared with OpenTelemetry)

**Sample Collector Client:**
- Configuration: `collector/config.yaml`
- Collector polls the server at `http://host.containers.internal:8000/v1/opamp` every 5 seconds via the `opampextension`
- Capabilities advertised by sample collector: `reports_effective_config`, `reports_health`, `reports_available_components`

## Data Storage

**Databases:** None

**File Storage:** None

**Caching:** None

## Authentication & Identity

**Auth Provider:** None — no authentication or authorisation is implemented on any endpoint.

The server assigns a hardcoded `instance_uid = b"server-1234"` in all `ServerToAgent` responses (`server.py` line 25). This is a placeholder and does not validate collector identity.

## Monitoring & Observability

**Error Tracking:** None (no external error tracking service)

**Logs:**
- Standard Python `logging` module, configured at `INFO` level in `server.py`
- Logger name: `opamp-server`
- Logs raw byte count of incoming message and the decoded protobuf object
- Errors logged at `ERROR` level on `DecodeError`

## CI/CD & Deployment

**Hosting:**
- Docker container; port `8000` exposed

**CI Pipeline:** None detected (no `.github/`, `.gitlab-ci.yml`, or similar)

## Environment Configuration

**Required env vars:** None — the server reads no environment variables at runtime.

**Env files:** None present (no `.env` detected)

**Secrets location:** N/A — no secrets required

## Webhooks & Callbacks

**Incoming:**
- `POST /v1/opamp` — receives `AgentToServer` protobuf messages from OpAMP agents (e.g. OpenTelemetry Collectors with `opampextension` enabled)

**Outgoing:** None

## Protocol Buffer Sources

The generated Python stubs (`opamp_pb2.py`, `anyvalue_pb2.py`) are derived from:
- `proto/opamp.proto` — main OpAMP message definitions; Go package path `github.com/open-telemetry/opamp-go/protobufs`
- `proto/anyvalue.proto` — shared OpenTelemetry `AnyValue`/`KeyValue` types

Protobuf compiler version used to generate stubs: **6.32.0**. If proto schemas are updated, stubs must be regenerated with a matching `protoc` version and the `protobuf>=6.0.0` Python runtime.

---

*Integration audit: 2026-03-27*
