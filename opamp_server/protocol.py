"""Pure OpAMP protocol helper functions.

All functions are stateless and side-effect free — they only construct
or parse protobuf messages. No I/O, no registry access.
"""
from __future__ import annotations

import uuid6
import opamp_pb2 as opamp

# Server capabilities advertised to agents in Phase 1:
# AcceptsStatus (0x01) | AcceptsEffectiveConfig (0x04)
SERVER_CAPABILITIES: int = 0x05

# ServerToAgentFlags bit masks
FLAG_REPORT_FULL_STATE: int = 0x01

# ServerErrorResponseType values (from opamp_pb2 enum)
ERROR_TYPE_BAD_REQUEST: int = 1
ERROR_TYPE_UNAVAILABLE: int = 2


def generate_server_uid() -> bytes:
    """Generate a UUID v7 as 16-byte binary for server startup identity.

    Returns:
        16-byte UUID v7 binary representation.
    """
    return uuid6.uuid7().bytes


def build_success_response(
    agent_uid: bytes,
    flags: int = 0,
) -> bytes:
    """Build a serialized ServerToAgent response for a successful request.

    Args:
        agent_uid: The agent's instance_uid bytes from AgentToServer.instance_uid.
            MUST be echoed back exactly as received.
        flags: Bit flags (e.g., FLAG_REPORT_FULL_STATE = 0x01).

    Returns:
        Serialized protobuf bytes ready to send as response body.
    """
    resp = opamp.ServerToAgent()
    resp.instance_uid = agent_uid
    resp.capabilities = SERVER_CAPABILITIES
    resp.flags = flags
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
