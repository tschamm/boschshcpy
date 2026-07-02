"""Tests for the Motion Detector II DetectionTest / LatestTamper / PollControl
setters + reset operation added for tschamm/boschshc-hass#325.

Mirrors the __new__-bypass + injected-state pattern used by test_sync_setters.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock


def _make_svc(cls, state_dict, atype="testType", sid=None):
    obj = cls.__new__(cls)
    raw = {
        "id": sid or cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": atype, **state_dict},
    }
    obj._api = None
    obj._raw_device_service = raw
    obj._raw_state = raw["state"]
    obj._last_update = None
    obj._callbacks = {}
    obj._event_callbacks = {}
    return obj


# ---------------------------------------------------------------------------
# DetectionTestService
# ---------------------------------------------------------------------------

class TestDetectionTestService:
    def _svc(self, **state):
        from boschshcpy.services_impl import DetectionTestService
        return _make_svc(
            DetectionTestService,
            state or {"detectionState": "DETECTION_TEST_STOPPED"},
            atype="detectionTestState",
        )

    def test_detection_state_getter(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = self._svc(detectionState="DETECTION_TEST_STARTED")
        assert svc.detection_state == (
            DetectionTestService.DetectionState.DETECTION_TEST_STARTED
        )

    def test_detection_state_missing_returns_unknown(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = _make_svc(DetectionTestService, {}, atype="detectionTestState")
        assert svc.detection_state == (
            DetectionTestService.DetectionState.DETECTION_TEST_UNKNOWN
        )

    def test_detection_state_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = self._svc(detectionState="WAT")
        assert svc.detection_state == (
            DetectionTestService.DetectionState.DETECTION_TEST_UNKNOWN
        )

    def test_set_request_start(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = self._svc()
        svc.put_state_element = MagicMock()
        svc.set_detection_state_request(
            DetectionTestService.DetectionStateRequest.DETECTION_STATE_START
        )
        # hass#325: must write the REQUEST field, not the read-only state.
        svc.put_state_element.assert_called_once_with(
            "detectionStateRequest", "DETECTION_STATE_START"
        )

    def test_async_set_request_stop(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = self._svc()
        svc.async_put_state_element = AsyncMock()
        asyncio.run(
            svc.async_set_detection_state_request(
                DetectionTestService.DetectionStateRequest.DETECTION_STATE_STOP
            )
        )
        svc.async_put_state_element.assert_awaited_once_with(
            "detectionStateRequest", "DETECTION_STATE_STOP"
        )

    # -----------------------------------------------------------------
    # motion_sensitivity: DetectionTestState's own motionSensitivity field
    # (APK: getMotionSensorSensitivity(), distinct from
    # PirSensorConfigurationService's field of the same name) — never observed
    # in a real rawscan yet, but the model class carries it so the property
    # must not silently drop it if/when a controller does report it.
    # -----------------------------------------------------------------

    def test_motion_sensitivity_getter(self):
        from boschshcpy.services_impl import (
            DetectionTestService,
            PirSensorConfigurationService,
        )
        svc = self._svc(
            detectionState="DETECTION_TEST_STOPPED", motionSensitivity="HIGH"
        )
        assert (
            svc.motion_sensitivity
            == PirSensorConfigurationService.MotionSensitivity.HIGH
        )

    def test_motion_sensitivity_missing_returns_unknown(self):
        from boschshcpy.services_impl import (
            DetectionTestService,
            PirSensorConfigurationService,
        )
        svc = _make_svc(
            DetectionTestService,
            {"detectionState": "DETECTION_TEST_STOPPED"},
            atype="detectionTestState",
        )
        assert (
            svc.motion_sensitivity
            == PirSensorConfigurationService.MotionSensitivity.UNKNOWN
        )

    def test_motion_sensitivity_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import (
            DetectionTestService,
            PirSensorConfigurationService,
        )
        svc = self._svc(
            detectionState="DETECTION_TEST_STOPPED", motionSensitivity="WAT"
        )
        assert (
            svc.motion_sensitivity
            == PirSensorConfigurationService.MotionSensitivity.UNKNOWN
        )


# ---------------------------------------------------------------------------
# LatestTamperService
# ---------------------------------------------------------------------------

class TestLatestTamperService:
    def _svc(self):
        from boschshcpy.services_impl import LatestTamperService
        return _make_svc(
            LatestTamperService,
            {"tamperProtectionEnabled": True, "wasTampered": False},
            atype="tamperState",
            sid="LatestTamper",
        )

    def test_protection_setter(self):
        svc = self._svc()
        svc.put_state_element = MagicMock()
        svc.tamper_protection_enabled = False
        svc.put_state_element.assert_called_once_with(
            "tamperProtectionEnabled", False
        )

    def test_async_protection_setter(self):
        svc = self._svc()
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_tamper_protection_enabled(True))
        svc.async_put_state_element.assert_awaited_once_with(
            "tamperProtectionEnabled", True
        )

    def test_reset_tampered_state_posts_operation(self):
        svc = self._svc()
        svc._api = MagicMock()
        svc.reset_tampered_state()
        svc._api.post_device_service_operation.assert_called_once_with(
            "test-device", "LatestTamper", "resetTamperedState"
        )

    def test_async_reset_tampered_state_posts_operation(self):
        svc = self._svc()
        svc._api = MagicMock()
        svc._api.post_device_service_operation = AsyncMock()
        asyncio.run(svc.async_reset_tampered_state())
        svc._api.post_device_service_operation.assert_awaited_once_with(
            "test-device", "LatestTamper", "resetTamperedState"
        )


# ---------------------------------------------------------------------------
# PollControlService
# ---------------------------------------------------------------------------

class TestPollControlService:
    def _svc(self, **state):
        from boschshcpy.services_impl import PollControlService
        return _make_svc(
            PollControlService,
            state or {"longPollInterval": "LONG"},
            atype="pollControlState",
        )

    def test_getter(self):
        from boschshcpy.services_impl import PollControlService
        svc = self._svc(longPollInterval="SHORT")
        assert svc.longPollInterval == PollControlService.PollControlState.SHORT

    def test_getter_bad_value_unknown(self):
        from boschshcpy.services_impl import PollControlService
        svc = self._svc(longPollInterval="WAT")
        assert svc.longPollInterval == PollControlService.PollControlState.UNKNOWN

    def test_setter(self):
        from boschshcpy.services_impl import PollControlService
        svc = self._svc()
        svc.put_state_element = MagicMock()
        svc.longPollInterval = PollControlService.PollControlState.SHORT
        svc.put_state_element.assert_called_once_with("longPollInterval", "SHORT")

    def test_async_setter(self):
        from boschshcpy.services_impl import PollControlService
        svc = self._svc()
        svc.async_put_state_element = AsyncMock()
        asyncio.run(
            svc.async_set_long_poll_interval(
                PollControlService.PollControlState.LONG
            )
        )
        svc.async_put_state_element.assert_awaited_once_with(
            "longPollInterval", "LONG"
        )


# ---------------------------------------------------------------------------
# api.post_device_service_operation URL building
# ---------------------------------------------------------------------------

def test_post_device_service_operation_url():
    from boschshcpy.api import SHCAPI
    api = SHCAPI.__new__(SHCAPI)
    api._api_root = "https://shc:8444/smarthome"
    api._post_api_or_fail = MagicMock(return_value={})
    api.post_device_service_operation("dev1", "LatestTamper", "resetTamperedState")
    api._post_api_or_fail.assert_called_once_with(
        "https://shc:8444/smarthome/devices/dev1/services/LatestTamper"
        "/operation/resetTamperedState",
        body=None,
    )


# ---------------------------------------------------------------------------
# SHCMotionDetector2 model delegation
# ---------------------------------------------------------------------------

class TestMotionDetector2Model:
    def _dev(self, with_detection=True):
        from boschshcpy.models_impl import SHCMotionDetector2
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._raw_device = {
            "id": "dev1",
            "deviceModel": "MD2",
            "manufacturer": "BOSCH",
            "name": "MD2",
            "profile": "GENERIC",
            "supportedProfiles": ["OUTDOOR", "GENERIC"],
        }
        obj._api = None
        obj._callbacks = {}
        obj._detectiontest_service = MagicMock() if with_detection else None
        obj._latesttamper_service = MagicMock()
        obj._pollcontrol_service = MagicMock()
        return obj

    def test_supports_detection_test(self):
        assert self._dev(with_detection=True).supports_detection_test is True
        assert self._dev(with_detection=False).supports_detection_test is False

    def test_supported_profiles_and_profile(self):
        dev = self._dev()
        assert dev.supported_profiles == ["OUTDOOR", "GENERIC"]
        assert dev.profile == "GENERIC"

    def test_set_detection_state_request_delegates(self):
        from boschshcpy.services_impl import DetectionTestService
        dev = self._dev()
        req = DetectionTestService.DetectionStateRequest.DETECTION_STATE_START
        dev.set_detection_state_request(req)
        dev._detectiontest_service.set_detection_state_request.assert_called_once_with(
            req
        )

    def test_set_detection_state_request_noop_without_service(self):
        from boschshcpy.services_impl import DetectionTestService
        dev = self._dev(with_detection=False)
        # must not raise when the service is absent
        dev.set_detection_state_request(
            DetectionTestService.DetectionStateRequest.DETECTION_STATE_STOP
        )

    def test_tamper_setter_delegates(self):
        dev = self._dev()
        dev.tamper_protection_enabled = False
        assert dev._latesttamper_service.tamper_protection_enabled is False

    def test_reset_tamper_delegates(self):
        dev = self._dev()
        dev.reset_tampered_state()
        dev._latesttamper_service.reset_tampered_state.assert_called_once_with()

    def test_long_poll_interval_setter_delegates(self):
        from boschshcpy.services_impl import PollControlService
        dev = self._dev()
        dev.long_poll_interval = PollControlService.PollControlState.SHORT
        assert (
            dev._pollcontrol_service.longPollInterval
            == PollControlService.PollControlState.SHORT
        )

    def test_async_reset_tamper_delegates(self):
        dev = self._dev()
        dev._latesttamper_service.async_reset_tampered_state = AsyncMock()
        asyncio.run(dev.async_reset_tampered_state())
        dev._latesttamper_service.async_reset_tampered_state.assert_awaited_once_with()
