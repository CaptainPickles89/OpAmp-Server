"""Integration tests for the /v1/opamp handler endpoint."""
from __future__ import annotations

import asyncio

import pytest
import opamp_pb2 as opamp

OPAMP_URL = "/v1/opamp"
PROTOBUF_CONTENT_TYPE = "application/x-protobuf"
HEADERS = {"Content-Type": PROTOBUF_CONTENT_TYPE}


class TestValidRequest:
    async def test_returns_protobuf_content_type(
        self, async_client, valid_agent_to_server_bytes
    ):
        """PROTO-04: All responses on /v1/opamp must use application/x-protobuf."""
        response = await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        assert response.status_code == 200
        assert "application/x-protobuf" in response.headers["content-type"]

    async def test_response_decodes_as_server_to_agent(
        self, async_client, valid_agent_to_server_bytes
    ):
        response = await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)  # must not raise
        assert msg is not None

    async def test_instance_uid_echoed_back(
        self, async_client, valid_agent_to_server_bytes, valid_agent_uid
    ):
        """PROTO-01: ServerToAgent.instance_uid MUST echo agent's UID."""
        response = await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert msg.instance_uid == valid_agent_uid

    async def test_capabilities_present_in_response(
        self, async_client, valid_agent_to_server_bytes
    ):
        """PROTO-03: ServerToAgent.capabilities MUST be 0x07 (AcceptsStatus | OffersRemoteConfig | AcceptsEffectiveConfig)."""
        response = await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert msg.capabilities == 0x07  # Phase 2: OffersRemoteConfig (0x02) added

    async def test_no_error_response_on_valid_request(
        self, async_client, valid_agent_to_server_bytes
    ):
        response = await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert not msg.HasField("error_response")


class TestSequenceGap:
    async def test_report_full_state_flag_set_on_gap(
        self, async_client, valid_agent_to_server_bytes, agent_to_server_with_gap
    ):
        """PROTO-02: ReportFullState flag (0x01) set when sequence gap detected."""
        # First request establishes sequence_num=1
        await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        # Second request with seq=5 (gap — expected 2)
        response = await async_client.post(
            OPAMP_URL, content=agent_to_server_with_gap, headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert msg.flags & 0x01 == 0x01  # ReportFullState bit set

    async def test_no_report_full_state_on_sequential(
        self, async_client, valid_agent_to_server_bytes, valid_agent_uid
    ):
        """PROTO-02: No ReportFullState flag when messages arrive sequentially."""
        await async_client.post(
            OPAMP_URL, content=valid_agent_to_server_bytes, headers=HEADERS
        )
        # Send seq=2 (sequential after seq=1)
        import opamp_pb2 as opamp
        msg = opamp.AgentToServer()
        msg.instance_uid = valid_agent_uid
        msg.sequence_num = 2
        msg.capabilities = 0x805

        response = await async_client.post(
            OPAMP_URL, content=msg.SerializeToString(), headers=HEADERS
        )
        resp_msg = opamp.ServerToAgent()
        resp_msg.ParseFromString(response.content)
        assert resp_msg.flags & 0x01 == 0  # ReportFullState NOT set


class TestErrorResponses:
    async def test_invalid_protobuf_returns_binary_error(self, async_client):
        """PROTO-04: Invalid body returns binary ServerErrorResponse, not JSON."""
        response = await async_client.post(
            OPAMP_URL, content=b"not valid protobuf bytes", headers=HEADERS
        )
        assert response.status_code == 200
        assert "application/x-protobuf" in response.headers["content-type"]
        # Must decode as ServerToAgent with error_response set
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert msg.HasField("error_response")
        # Must NOT be JSON
        assert not response.content.startswith(b"{")

    async def test_invalid_protobuf_error_response_has_message(self, async_client):
        response = await async_client.post(
            OPAMP_URL, content=b"\xff\xfe\xfd", headers=HEADERS
        )
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert len(msg.error_response.error_message) > 0

    async def test_oversized_body_returns_binary_error(self, async_client):
        """PROTO-05: Body exceeding max_body_size returns binary ServerErrorResponse."""
        # Default max is 1MB — send 2MB
        oversized_body = b"x" * (2 * 1024 * 1024)
        response = await async_client.post(
            OPAMP_URL,
            content=oversized_body,
            headers={**HEADERS, "Content-Length": str(len(oversized_body))},
        )
        assert "application/x-protobuf" in response.headers["content-type"]
        msg = opamp.ServerToAgent()
        msg.ParseFromString(response.content)
        assert msg.HasField("error_response")


# ---------------------------------------------------------------------------
# Phase 9 stubs — handler extracts non_identifying_attributes (COLS-01)
# ---------------------------------------------------------------------------


class TestResourceAttrExtraction:
    async def test_handler_extracts_resource_attrs_from_agent_description(
        self, async_client, tmp_path
    ):
        """COLS-01: Handler writes non_identifying_attributes to agent_resource_attrs table."""
        import aiosqlite
        import opamp_pb2 as opamp

        msg = opamp.AgentToServer()
        msg.instance_uid = b"\xaa" * 16
        msg.sequence_num = 1
        msg.capabilities = 0x805
        kv1 = msg.agent_description.non_identifying_attributes.add()
        kv1.key = "host.name"
        kv1.value.string_value = "web-01"
        kv2 = msg.agent_description.non_identifying_attributes.add()
        kv2.key = "os.type"
        kv2.value.string_value = "linux"

        response = await async_client.post(
            "/v1/opamp",
            content=msg.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
        )
        assert response.status_code == 200
        # Wait for fire-and-forget upsert_resource_attrs (thread-backed aiosqlite) to complete.
        pending = [
            t for t in asyncio.all_tasks()
            if t is not asyncio.current_task()
            and "upsert_resource_attrs" in str(t.get_coro())
        ]
        if pending:
            await asyncio.wait(pending, timeout=1.0)

        db_path = async_client.app.state.db_path  # type: ignore[attr-defined]
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT key, value FROM agent_resource_attrs WHERE instance_uid = ? ORDER BY key",
                ((b"\xaa" * 16).hex(),),
            ) as cursor:
                rows = await cursor.fetchall()
        assert len(rows) == 2
        assert ("host.name", "web-01") in rows
        assert ("os.type", "linux") in rows

    async def test_handler_ignores_empty_agent_description(self, async_client, tmp_path):
        """COLS-01: Handler writes no rows when non_identifying_attributes is empty."""
        import aiosqlite
        import opamp_pb2 as opamp

        msg = opamp.AgentToServer()
        msg.instance_uid = b"\xbb" * 16
        msg.sequence_num = 1
        msg.capabilities = 0x805
        # agent_description present but non_identifying_attributes empty
        msg.agent_description.SetInParent()

        response = await async_client.post(
            "/v1/opamp",
            content=msg.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
        )
        assert response.status_code == 200

        db_path = async_client.app.state.db_path  # type: ignore[attr-defined]
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM agent_resource_attrs WHERE instance_uid = ?",
                ((b"\xbb" * 16).hex(),),
            ) as cursor:
                count = (await cursor.fetchone())[0]
        assert count == 0
