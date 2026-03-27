"""Unit tests for Settings configuration loading."""
from __future__ import annotations

import pytest


class TestSettings:
    def test_default_host_is_0000(self):
        """OPS-03: Default host is 0.0.0.0 for container deployment."""
        from opamp_server.config import Settings
        s = Settings()
        assert s.host == "0.0.0.0"

    def test_host_overridden_by_env(self, monkeypatch):
        """OPS-03: OPAMP_HOST env var overrides default."""
        monkeypatch.setenv("OPAMP_HOST", "127.0.0.1")
        from opamp_server.config import Settings
        s = Settings()
        assert s.host == "127.0.0.1"

    def test_default_max_body_size(self):
        """PROTO-05: Default max body size is 1MB."""
        from opamp_server.config import Settings
        s = Settings()
        assert s.max_body_size == 1_048_576

    def test_default_rate_limit(self):
        """PROTO-06: Default rate limit is 100/minute."""
        from opamp_server.config import Settings
        s = Settings()
        assert s.rate_limit == "100/minute"

    def test_default_db_path(self):
        """REGST-02: Default db_path for SQLite registry."""
        from opamp_server.config import Settings
        s = Settings()
        assert "registry.db" in s.db_path

    def test_health_snapshot_retention_default(self):
        from opamp_server.config import Settings
        s = Settings()
        assert s.health_snapshot_retention == 1000
