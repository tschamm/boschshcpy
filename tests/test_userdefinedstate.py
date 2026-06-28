"""Regression tests for SHCUserDefinedState — covers #351 (KeyError: 'deleted')."""

from unittest.mock import MagicMock

import pytest

from boschshcpy.userdefinedstate import SHCUserDefinedState


def _make_uds(raw):
    api = MagicMock()
    info = MagicMock()
    info.macAddress = "AA:BB:CC:DD:EE:FF"
    return SHCUserDefinedState(api=api, info=info, raw_state=raw)


class TestDeletedProperty:
    def test_deleted_absent_returns_false(self):
        """API omits 'deleted' when False — must not raise KeyError (#351)."""
        uds = _make_uds({"id": "u1", "name": "Test", "state": True})
        assert uds.deleted is False

    def test_deleted_true(self):
        uds = _make_uds({"id": "u1", "name": "Test", "state": True, "deleted": True})
        assert uds.deleted is True

    def test_deleted_false_explicit(self):
        uds = _make_uds({"id": "u1", "name": "Test", "state": True, "deleted": False})
        assert uds.deleted is False


class TestStateProperty:
    def test_state_absent_returns_false(self):
        """Sparse deletion payload may omit 'state' — must not raise KeyError."""
        uds = _make_uds({"id": "u1", "name": "Test", "deleted": True})
        assert uds.state is False

    def test_state_true(self):
        uds = _make_uds({"id": "u1", "name": "Test", "state": True})
        assert uds.state is True

    def test_state_false(self):
        uds = _make_uds({"id": "u1", "name": "Test", "state": False})
        assert uds.state is False


class TestOtherProperties:
    def test_id(self):
        uds = _make_uds({"id": "u42", "name": "X", "state": False})
        assert uds.id == "u42"

    def test_name(self):
        uds = _make_uds({"id": "u1", "name": "Vacation", "state": False})
        assert uds.name == "Vacation"

    def test_root_device_id(self):
        uds = _make_uds({"id": "u1", "name": "X", "state": False})
        assert uds.root_device_id == "AA:BB:CC:DD:EE:FF"
