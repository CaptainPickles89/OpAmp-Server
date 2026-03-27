"""Pure OpAMP protocol helper functions.

All functions are stateless and side-effect free — they only construct
or parse protobuf messages. No I/O, no registry access.
"""
from __future__ import annotations

import hashlib

import uuid6
import opamp_pb2 as opamp

# Server capabilities advertised to agents — Phase 2 adds OffersRemoteConfig (0x02):
# AcceptsStatus (0x01) | OffersRemoteConfig (0x02) | AcceptsEffectiveConfig (0x04) = 0x07
SERVER_CAPABILITIES: int = 0x07

# ServerToAgentFlags bit masks
FLAG_REPORT_FULL_STATE: int = 0x01

# ServerErrorResponseType values (from opamp_pb2 enum)
ERROR_TYPE_BAD_REQUEST: int = 1
ERROR_TYPE_UNAVAILABLE: int = 2

# AgentCapabilities bits (from opamp spec)
CAPABILITY_ACCEPTS_REMOTE_CONFIG: int = 0x02


def generate_server_uid() -> bytes:
    """Generate a UUID v7 as 16-byte binary for server startup identity.

    Returns:
        16-byte UUID v7 binary representation.
    """
    return uuid6.uuid7().bytes


def compute_config_hash(config_body: str) -> bytes:
    """Compute SHA-256 hash of config body as raw bytes.

    The resulting bytes are stored in AgentRemoteConfig.config_hash.
    The hex string (.hex()) is stored in SQLite.

    Args:
        config_body: Raw YAML string to hash.

    Returns:
        32-byte SHA-256 digest (raw bytes, not hex).
    """
    return hashlib.sha256(config_body.encode("utf-8")).digest()


def build_remote_config(
    config_body: str,
    config_hash: bytes,
) -> "opamp.AgentRemoteConfig":
    """Build an AgentRemoteConfig for a YAML config push.

    Constructs the nested AgentConfigMap -> AgentConfigFile structure
    required by the OpAMP spec, using "collector.yaml" as the canonical
    map key for OTel Collector configs.

    Args:
        config_body: Raw YAML string to deliver to the agent.
        config_hash: Pre-computed SHA-256 bytes (32 bytes) from compute_config_hash().

    Returns:
        AgentRemoteConfig ready to attach to ServerToAgent.remote_config.
    """
    cfg_file = opamp.AgentConfigFile()
    cfg_file.body = config_body.encode("utf-8")
    cfg_file.content_type = "text/yaml"

    cfg_map = opamp.AgentConfigMap()
    cfg_map.config_map["collector.yaml"].CopyFrom(cfg_file)

    remote_cfg = opamp.AgentRemoteConfig()
    remote_cfg.config.CopyFrom(cfg_map)
    remote_cfg.config_hash = config_hash
    return remote_cfg


def build_success_response(
    agent_uid: bytes,
    flags: int = 0,
    remote_config: "opamp.AgentRemoteConfig | None" = None,
) -> bytes:
    """Build a serialized ServerToAgent response for a successful request.

    Args:
        agent_uid: The agent's instance_uid bytes from AgentToServer.instance_uid.
            MUST be echoed back exactly as received.
        flags: Bit flags (e.g., FLAG_REPORT_FULL_STATE = 0x01).
        remote_config: Optional AgentRemoteConfig to include in response.
            Pass None for normal responses without a pending config push.

    Returns:
        Serialized protobuf bytes ready to send as response body.
    """
    resp = opamp.ServerToAgent()
    resp.instance_uid = agent_uid
    resp.capabilities = SERVER_CAPABILITIES
    resp.flags = flags
    if remote_config is not None:
        resp.remote_config.CopyFrom(remote_config)
    return resp.SerializeToString()


def build_error_response(
    error_type: int,
    error_message: str,
    agent_uid: bytes = b"",
) -> bytes:
    """Build a serialized ServerToAgent containing a ServerErrorResponse.

    Per spec: when error_response is set, all other fields MUST be unset.

    Args:
        error_type: ERROR_TYPE_BAD_REQUEST (1) or ERROR_TYPE_UNAVAILABLE (2).
        error_message: Human-readable error description.
        agent_uid: Agent UID if known; empty bytes if request could not be parsed.

    Returns:
        Serialized protobuf bytes ready to send as error response body.
    """
    err = opamp.ServerErrorResponse()
    err.type = error_type
    err.error_message = error_message

    resp = opamp.ServerToAgent()
    # Per spec: when error_response set, instance_uid is still set for routing
    if agent_uid:
        resp.instance_uid = agent_uid
    resp.error_response.CopyFrom(err)
    # NOTE: capabilities and flags MUST NOT be set when error_response is set
    return resp.SerializeToString()


def detect_sequence_gap(received_seq: int, stored_seq: int | None) -> bool:
    """Determine whether a sequence number gap has occurred.

    Args:
        received_seq: sequence_num from the incoming AgentToServer.
        stored_seq: Last known sequence_num for this agent, or None if first message.

    Returns:
        True if a gap is detected (ReportFullState should be requested).
    """
    if stored_seq is None:
        # First message from this agent — no gap possible
        return False
    return received_seq != stored_seq + 1


def parse_agent_uid(msg: opamp.AgentToServer) -> bytes:
    """Extract agent instance_uid from parsed AgentToServer message.

    Args:
        msg: Parsed AgentToServer protobuf message.

    Returns:
        Raw bytes of the agent's instance_uid (16 bytes for valid UUID v7).
    """
    return msg.instance_uid
