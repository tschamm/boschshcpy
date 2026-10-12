"""Sync calibration writes match async payloads without hardware."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import AsyncMock, MagicMock

import pytest

from boschshcpy.models_impl import SHCHeatingCircuit, SHCMicromoduleDimmer
from boschshcpy.services_impl import DimmerConfigurationService, HeatingCircuitService


def make_service(cls=DimmerConfigurationService, state=None, api=None):
    return cls(
        api=api if api is not None else MagicMock(),
        raw_device_service={
            "id": "DimmerConfiguration"
            if cls is DimmerConfigurationService
            else "HeatingCircuit",
            "deviceId": "d#1",
            "state": {
                "@type": "testState",
                **(
                    state
                    if state is not None
                    else {
                        "edgePhaseControlMode": "TRAILING",
                        "dimmingSpeed": 5,
                        "brightnessRange": {"minBrightness": 10, "maxBrightness": 90},
                    }
                ),
            },
        },
    )


@pytest.mark.parametrize(
    "method,args,kwargs",
    [
        (
            "set_edge_phase_control_mode",
            (DimmerConfigurationService.EdgePhaseControlMode.LEADING,),
            {},
        ),
        ("set_dimming_speed", (7.9,), {}),
        ("set_brightness_range", (), {"min_brightness": 20}),
        ("set_brightness_range", (), {"max_brightness": 80}),
        ("set_brightness_range", (), {"min_brightness": 0, "max_brightness": 100}),
        ("set_brightness_range", (), {}),
    ],
)
def test_dimmer_sync_async_payload_parity(method, args, kwargs):
    sync_api = MagicMock()
    async_api = MagicMock(put_device_service_state=AsyncMock())
    sync_svc = make_service(api=sync_api)
    async_svc = make_service(api=async_api)
    getattr(sync_svc, method)(*args, **kwargs)
    asyncio.run(getattr(async_svc, "async_" + method)(*args, **kwargs))
    assert (
        sync_api.put_device_service_state.call_args
        == async_api.put_device_service_state.await_args
    )
    assert sync_api.put_device_service_state.call_args.args[:2] == (
        "d%231",
        "DimmerConfiguration",
    )
    assert sync_svc.min_brightness == 10  # writes do not replace cached state


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_brightness": 90},
        {"max_brightness": 10},
        {"min_brightness": 70, "max_brightness": 60},
    ],
)
def test_invalid_range_matches_async_validation(kwargs):
    sync_svc, async_svc = make_service(), make_service()
    with pytest.raises(ValueError) as sync_error:
        sync_svc.set_brightness_range(**kwargs)
    with pytest.raises(ValueError) as async_error:
        asyncio.run(async_svc.async_set_brightness_range(**kwargs))
    assert str(sync_error.value) == str(async_error.value)
    sync_svc._api.put_device_service_state.assert_not_called()


def ranges(svc):
    return [
        call.args[2]["brightnessRange"]
        for call in svc._api.put_device_service_state.call_args_list
    ]


def push(svc):
    svc.process_long_polling_poll_result(
        {
            "@type": "DeviceServiceData",
            "id": "DimmerConfiguration",
            "deviceId": "d#1",
            "state": {
                "@type": "testState",
                "brightnessRange": {"minBrightness": 5, "maxBrightness": 95},
            },
        }
    )


def test_sequential_partial_ranges_preserve_written_bound():
    svc = make_service()
    svc.set_brightness_range(min_brightness=20)
    svc.set_brightness_range(max_brightness=80)
    assert ranges(svc) == [
        {"minBrightness": 20, "maxBrightness": 90},
        {"minBrightness": 20, "maxBrightness": 80},
    ]


def test_concurrent_partial_ranges_serialize_io_and_merge():
    svc = make_service()
    in_put, release_put, second_started, second_in_put = (Event() for _ in range(4))

    def put(*args):
        if args[2]["brightnessRange"]["minBrightness"] == 20 and not in_put.is_set():
            in_put.set()
            assert release_put.wait(5)
        else:
            second_in_put.set()

    def second_write():
        second_started.set()
        svc.set_brightness_range(max_brightness=80)

    svc._api.put_device_service_state.side_effect = put
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(svc.set_brightness_range, min_brightness=20)
        try:
            assert in_put.wait(5)
            second = executor.submit(second_write)
            assert second_started.wait(5)
            assert not second_in_put.wait(0.1)
        finally:
            release_put.set()
        first.result(timeout=5)
        second.result(timeout=5)
    assert ranges(svc)[-1] == {"minBrightness": 20, "maxBrightness": 80}


@pytest.mark.parametrize("during_put", [False, True])
def test_pushed_state_supersedes_written_range(during_put):
    svc = make_service()
    if during_put:
        svc._api.put_device_service_state.side_effect = lambda *_: push(svc)
    svc.set_brightness_range(min_brightness=20)
    if not during_put:
        push(svc)
    svc._api.put_device_service_state.side_effect = None
    svc.set_brightness_range(max_brightness=80)
    assert ranges(svc)[-1] == {"minBrightness": 5, "maxBrightness": 80}


def test_failed_put_does_not_cache_written_bounds():
    svc = make_service()
    svc._api.put_device_service_state.side_effect = RuntimeError("PUT failed")
    with pytest.raises(RuntimeError, match="PUT failed"):
        svc.set_brightness_range(min_brightness=20)
    svc._api.put_device_service_state.side_effect = None
    svc.set_brightness_range(max_brightness=80)
    assert ranges(svc)[-1] == {"minBrightness": 10, "maxBrightness": 80}


def test_missing_range_uses_async_defaults():
    svc = make_service(state={})
    svc.set_brightness_range(min_brightness=20)
    assert ranges(svc) == [{"minBrightness": 20, "maxBrightness": 100}]


@pytest.mark.parametrize("via_property", [False, True])
def test_dimmer_scalar_properties_and_device_delegates(via_property):
    svc = make_service()
    device = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
    device._dimmerconfig_service = svc
    mode = DimmerConfigurationService.EdgePhaseControlMode.LEADING
    assert device.dimming_speed == 5
    assert (
        device.edge_phase_control_mode
        == DimmerConfigurationService.EdgePhaseControlMode.TRAILING
    )
    for obj in (svc, device):
        if via_property:
            obj.edge_phase_control_mode = mode
            obj.dimming_speed = 7
        else:
            obj.set_edge_phase_control_mode(mode)
            obj.set_dimming_speed(7)
    device.set_brightness_range(min_brightness=20, max_brightness=80)
    payloads = [c.args[2] for c in svc._api.put_device_service_state.call_args_list]
    assert payloads == [
        {"@type": "testState", "edgePhaseControlMode": "LEADING"},
        {"@type": "testState", "dimmingSpeed": 7},
    ] * 2 + [
        {
            "@type": "testState",
            "brightnessRange": {"minBrightness": 20, "maxBrightness": 80},
        }
    ]


def test_dimmer_device_without_configuration():
    device = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
    device._dimmerconfig_service = None
    device.set_edge_phase_control_mode(
        DimmerConfigurationService.EdgePhaseControlMode.LEADING
    )
    device.set_dimming_speed(7)
    device.set_brightness_range(min_brightness=20)
    device.dimming_speed = 6
    device.edge_phase_control_mode = (
        DimmerConfigurationService.EdgePhaseControlMode.TRAILING
    )
    assert device.dimming_speed is None
    assert device.edge_phase_control_mode is None


@pytest.mark.parametrize(
    "level,key",
    [
        ("eco", "setpointTemperatureForLevelEco"),
        ("comfort", "setpointTemperatureForLevelComfort"),
    ],
)
def test_heating_service_and_device_match_async_payload(level, key):
    svc = make_service(HeatingCircuitService, state={})
    device = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
    device._heating_circuit_service = svc
    method = "set_setpoint_temperature_" + level
    getattr(svc, method)(19.5)
    getattr(device, method)(19.5)
    setattr(svc, "setpoint_temperature_" + level, 19.5)
    svc._api.put_device_service_state.assert_called_with(
        "d%231", "HeatingCircuit", {"@type": "testState", key: 19.5}
    )
    assert svc._api.put_device_service_state.call_count == 3
    async_api = MagicMock(put_device_service_state=AsyncMock())
    device._heating_circuit_service = make_service(
        HeatingCircuitService, state={}, api=async_api
    )
    asyncio.run(getattr(device, "async_" + method)(19.5))
    assert (
        async_api.put_device_service_state.await_args
        == svc._api.put_device_service_state.call_args
    )
