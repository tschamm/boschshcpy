"""Tests for boschshcpy.zigbee_routing — SHCZigbeeRoutingInfo/ZigbeeRoutingQuality.

Covers the /smarthome/zigbee/routinginfo/{deviceId} endpoint model (APK
ground-truth, not in the official OpenAPI docs).
"""

from boschshcpy.zigbee_routing import (
    SHCZigbeeRoutingInfo,
    ZigbeeRoutingHop,
    ZigbeeRoutingQuality,
)


class TestZigbeeRoutingQuality:
    def test_all_known_values_parse(self):
        for raw in (
            "GOOD",
            "MEDIUM",
            "BAD",
            "NO_CONNECTION",
            "DEVICE_NOT_INITIALIZED",
            "NOT_SUPPORTED",
            "UNKNOWN",
        ):
            assert ZigbeeRoutingQuality(raw).value == raw

    def test_unknown_string_falls_back_to_unknown(self):
        # Robust parsing: the controller may one day report a value not yet
        # modeled here — must not raise ValueError (same pattern as
        # CommunicationQualityService.value / SHCInformation.updateState).
        assert ZigbeeRoutingQuality("SOME_NEW_VALUE") is ZigbeeRoutingQuality.UNKNOWN

    def test_none_falls_back_to_unknown(self):
        assert ZigbeeRoutingQuality(None) is ZigbeeRoutingQuality.UNKNOWN


class TestSHCZigbeeRoutingInfoNormalResponse:
    def _make(self):
        raw = {
            "device": "hdm:ZigBee:0123456789abcdef",
            "aggregatedQuality": "GOOD",
            "route": [
                {"deviceId": "hdm:ZigBee:0123456789abcdef", "quality": "GOOD"},
                {"deviceId": "hdm:ZigBee:routerplug01", "quality": "GOOD"},
            ],
        }
        return SHCZigbeeRoutingInfo(raw)

    def test_device_id(self):
        assert self._make().device_id == "hdm:ZigBee:0123456789abcdef"

    def test_aggregated_quality(self):
        assert self._make().aggregated_quality is ZigbeeRoutingQuality.GOOD

    def test_route_is_ordered_hop_list(self):
        info = self._make()
        assert info.route == [
            ZigbeeRoutingHop("hdm:ZigBee:0123456789abcdef", ZigbeeRoutingQuality.GOOD),
            ZigbeeRoutingHop("hdm:ZigBee:routerplug01", ZigbeeRoutingQuality.GOOD),
        ]

    def test_hop_attribute_access(self):
        hop = self._make().route[0]
        assert hop.device_id == "hdm:ZigBee:0123456789abcdef"
        assert hop.quality is ZigbeeRoutingQuality.GOOD


class TestSHCZigbeeRoutingInfoNoConnection:
    def _make(self):
        raw = {
            "device": "hdm:ZigBee:unreachable",
            "aggregatedQuality": "NO_CONNECTION",
            "route": [],
        }
        return SHCZigbeeRoutingInfo(raw)

    def test_aggregated_quality_no_connection(self):
        assert self._make().aggregated_quality is ZigbeeRoutingQuality.NO_CONNECTION

    def test_route_is_empty_list(self):
        assert self._make().route == []


class TestSHCZigbeeRoutingInfoUnknownHopQuality:
    def test_unknown_quality_string_in_hop_falls_back(self):
        raw = {
            "device": "hdm:ZigBee:abc",
            "aggregatedQuality": "GOOD",
            "route": [{"deviceId": "hdm:ZigBee:abc", "quality": "SOME_FUTURE_VALUE"}],
        }
        info = SHCZigbeeRoutingInfo(raw)
        assert info.route[0].quality is ZigbeeRoutingQuality.UNKNOWN

    def test_unknown_aggregated_quality_string_falls_back(self):
        raw = {"device": "hdm:ZigBee:abc", "aggregatedQuality": "SOME_FUTURE_VALUE", "route": []}
        info = SHCZigbeeRoutingInfo(raw)
        assert info.aggregated_quality is ZigbeeRoutingQuality.UNKNOWN


class TestSHCZigbeeRoutingInfoSparsePayload:
    def test_missing_fields_do_not_raise(self):
        info = SHCZigbeeRoutingInfo({})
        assert info.device_id == ""
        assert info.aggregated_quality is ZigbeeRoutingQuality.UNKNOWN
        assert info.route == []

    def test_summary_does_not_raise(self, capsys):
        raw = {
            "device": "hdm:ZigBee:abc",
            "aggregatedQuality": "GOOD",
            "route": [{"deviceId": "hdm:ZigBee:abc", "quality": "GOOD"}],
        }
        SHCZigbeeRoutingInfo(raw).summary()
        out = capsys.readouterr().out
        assert "hdm:ZigBee:abc" in out
        assert "GOOD" in out
