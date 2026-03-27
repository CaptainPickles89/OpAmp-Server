"""Unit tests for opamp_server.protocol — stateless protocol helpers."""
from __future__ import annotations

import opamp_pb2 as opamp
from opamp_server.protocol import (
    FLAG_REPORT_FULL_STATE,
    SERVER_CAPABILITIES,
    build_error_response,
    build_success_response,
    detect_sequence_gap,
    generate_server_uid,
)

TEST_UID = b"\x01" * 16  # 16-byte test agent UID


class TestGenerateServerUid:
    def test_returns_16_bytes(self):
        uid = generate_server_uid()
        assert len(uid) == 16

    def test_each_call_returns_different_uid(self):
        uid1 = generate_server_uid()
        uid2 = generate_server_uid()
        assert uid1 != uid2


class TestBuildSuccessResponse:
    def test_instance_uid_echoes_agent_uid(self):
        """PROTO-01: ServerToAgent.instance_uid MUST match AgentToServer.instance_uid."""
        raw = build_success_response(agent_uid=TEST_UID)
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.instance_uid == TEST_UID

    def test_capabilities_set_to_server_capabilities(self):
        """PROTO-03: ServerToAgent.capabilities MUST be set."""
        raw = build_success_response(agent_uid=TEST_UID)
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.capabilities == SERVER_CAPABILITIES
        assert resp.capabilities == 0x07  # Phase 2: OffersRemoteConfig (0x02) added

    def test_flags_default_to_zero(self):
        raw = build_success_response(agent_uid=TEST_UID)
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.flags == 0

    def test_flags_report_full_state_when_set(self):
        """PROTO-02: flags=ReportFullState (0x01) when sequence gap detected."""
        raw = build_success_response(agent_uid=TEST_UID, flags=FLAG_REPORT_FULL_STATE)
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.flags & FLAG_REPORT_FULL_STATE == FLAG_REPORT_FULL_STATE

    def test_no_error_response_on_success(self):
        raw = build_success_response(agent_uid=TEST_UID)
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert not resp.HasField("error_response")


class TestBuildErrorResponse:
    def test_error_response_field_set(self):
        """PROTO-04: Error path MUST use ServerErrorResponse, not JSON."""
        raw = build_error_response(error_type=1, error_message="bad request")
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.HasField("error_response")

    def test_error_type_is_set(self):
        raw = build_error_response(error_type=1, error_message="test error")
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.error_response.type == 1

    def test_error_message_is_set(self):
        raw = build_error_response(error_type=1, error_message="specific error message")
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.error_response.error_message == "specific error message"

    def test_capabilities_not_set_on_error(self):
        """Per spec: when error_response is set, capabilities MUST NOT be set."""
        raw = build_error_response(error_type=1, error_message="err")
        resp = opamp.ServerToAgent()
        resp.ParseFromString(raw)
        assert resp.capabilities == 0  # must be unset (default 0)


class TestDetectSequenceGap:
    def test_no_gap_on_first_message(self):
        """PROTO-02: First message from agent (stored_seq=None) is never a gap."""
        assert detect_sequence_gap(received_seq=1, stored_seq=None) is False

    def test_no_gap_when_sequential(self):
        assert detect_sequence_gap(received_seq=5, stored_seq=4) is False

    def test_gap_detected_when_skipped(self):
        """PROTO-02: seq=5 after seq=1 is a gap (expected 2)."""
        assert detect_sequence_gap(received_seq=5, stored_seq=1) is True

    def test_gap_detected_on_wrap_around(self):
        assert detect_sequence_gap(received_seq=0, stored_seq=5) is True

    def test_no_gap_at_zero_start(self):
        assert detect_sequence_gap(received_seq=0, stored_seq=None) is False
