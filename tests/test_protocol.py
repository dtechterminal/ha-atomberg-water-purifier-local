import json

import pytest

from purifier.protocol import decode_message, validate_command
from helpers import DEVICE, wire


def test_full_w2_state_and_sleep_time_comparison():
    device, state = decode_message(wire())
    assert device == DEVICE
    assert state.settings == {"mode": 3, "fallback_mode": 2, "idle_sleep": 0,
                              "tds_threshold": 250, "sleep_mode": 1,
                              "start_utc": 1767304800, "stop_utc": 1767330000}
    assert state.matches({"mode": 3, "start_utc": 1767304800 + 86400})
    assert not state.matches({"mode": 0})


@pytest.mark.parametrize("payload", [b"", b"garbage", b"ab" * 5000,
    json.dumps({"device_id": DEVICE, "state_string": "No command detected in the message"}).encode().hex().encode(),
    wire(changes={2: "S2"}), wire(changes={6: "nan"}), wire(changes={17: 999}),
    wire(changes={30: 3}), wire(changes={32: 0}), wire(changes={55: -1}),
    wire(device="not-an-id"), b"5b5d"])
def test_rejects_wrong_series_invalid_values_and_error_replies(payload):
    assert decode_message(payload) is None


def test_only_purifier_beacons_are_discovered():
    assert decode_message(b"020000000001_W2") == (DEVICE, None)
    assert decode_message(b"020000000001_S2") is None


@pytest.mark.parametrize("command", [{"reset": 1}, {"mode": 5}, {"mode": True},
    {"tds_threshold": 99}, {"tds_threshold": 301}, {"idle_sleep": "1"},
    {"fallback_mode": 1}, {"mode": 0, "idle_sleep": 1}, {"sleep_mode": 1},
    {"sleep_mode": 0, "start_utc": 10, "stop_utc": 20},
    {"sleep_mode": 1, "start_utc": -1, "stop_utc": 20}, {"read": 0}, {}])
def test_rejects_unsupported_or_incomplete_commands(command):
    with pytest.raises(ValueError):
        validate_command(command)
