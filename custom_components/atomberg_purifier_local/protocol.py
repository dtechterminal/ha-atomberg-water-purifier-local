"""Atomberg W2 local protocol. Settings offsets verified on a real W2.

No credentials, cloud requests, remote shells or third-party packages are used.
Unmapped telemetry is deliberately not presented as a named measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re

COMMAND_PORT = 5600
STATE_PORT = 5625
MODES = {
    0: "RO + UV",
    1: "Adaptive",
    2: "TasteTune 50–100 ppm",
    3: "TasteTune 75–125 ppm",
    4: "TasteTune 100–150 ppm",
    10: "Vacay",
}
FALLBACK_MODES = {key: MODES[key] for key in (0, 2, 3, 4)}
SETTING_FIELDS = {
    "mode": 17,
    "fallback_mode": 28,
    "idle_sleep": 30,
    "tds_threshold": 32,
    "sleep_mode": 53,
    "start_utc": 54,
    "stop_utc": 55,
}


def normalize_device_id(value: str) -> str:
    value = value.lower().replace(":", "").replace("-", "")
    if not re.fullmatch(r"[0-9a-f]{12}", value):
        raise ValueError("Invalid Atomberg device ID")
    return value


@dataclass(frozen=True)
class State:
    device_id: str
    fields: tuple[str, ...]

    def counter(self, index: int) -> float | None:
        """Reject invalid optional analytics without losing the device controls."""
        try:
            value = float(self.fields[index])
        except (IndexError, ValueError, TypeError):
            return None
        return value if math.isfinite(value) and 0 <= value <= 1e12 else None

    @property
    def lifetime_water(self) -> float | None:
        value = self.counter(19)
        return None if value is None else value / 1000

    @property
    def water_saved(self) -> float | None:
        ro, uf = self.counter(24), self.counter(25)
        return None if ro is None or uf is None else (ro * 1.5 + uf * 3) / 1000

    @property
    def runtime(self) -> float | None:
        value = self.counter(26)
        return None if value is None else value / 3600

    @property
    def settings(self) -> dict[str, int]:
        return {key: int(self.fields[index]) for key, index in SETTING_FIELDS.items()}

    def matches(self, expected: dict[str, int]) -> bool:
        actual = self.settings
        return all(
            actual[key] % 86400 == value % 86400
            if key in ("start_utc", "stop_utc") else actual[key] == value
            for key, value in expected.items()
        )


def decode_message(data: bytes) -> tuple[str, State | None] | None:
    """Decode a W2 beacon or a complete status; reject fan and error messages."""
    if not data or len(data) > 8192:
        return None
    try:
        text = data.decode("ascii").strip()
        if re.fullmatch(r"[0-9a-fA-F]{12}_W2", text):
            return normalize_device_id(text[:12]), None
        message = json.loads(bytes.fromhex(text))
        if not isinstance(message, dict):
            return None
        device_id = normalize_device_id(message["device_id"])
        fields = tuple(message["state_string"].split(","))
        if len(fields) < 57 or fields[2] != "W2" or fields[-1] != "END":
            return None
        for index, value in enumerate(fields[:-1]):
            # Optional beta counters are validated independently by counter().
            # A bad analytics value must not take the working controls offline.
            if index in (1, 2, 19, 24, 25, 26):
                continue
            if not math.isfinite(float(value)):
                return None
        state = State(device_id, fields)
        settings = state.settings
        # Validate settings independently of the command's one-key restriction.
        for key in ("mode", "fallback_mode", "idle_sleep", "tds_threshold"):
            validate_command({key: settings[key]})
        validate_command({key: settings[key] for key in ("sleep_mode", "start_utc", "stop_utc")}
                         if settings["sleep_mode"] else {"sleep_mode": 0})
        if not all(0 <= settings[k] <= 0xFFFFFFFF for k in ("start_utc", "stop_utc")):
            return None
        return device_id, state
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError):
        return None


def validate_command(command: dict) -> dict[str, int]:
    """Only documented settings; never allow reset, calibration or raw commands."""
    if not isinstance(command, dict) or not command:
        raise ValueError("A setting is required")
    if any(type(value) is not int for value in command.values()):
        raise ValueError("Setting values must be integers")
    if set(command) == {"read"} and command["read"] == 1:
        return dict(command)
    if "sleep_mode" in command:
        enabled = command["sleep_mode"]
        keys = {"sleep_mode", "start_utc", "stop_utc"} if enabled == 1 else {"sleep_mode"}
        if enabled not in (0, 1) or set(command) != keys:
            raise ValueError("An enabled sleep window requires both start and stop times")
        if any(not 0 <= command[key] <= 0xFFFFFFFF for key in keys - {"sleep_mode"}):
            raise ValueError("Sleep times must be valid epoch seconds")
        return dict(command)
    if len(command) != 1:
        raise ValueError("The purifier accepts one setting at a time")
    key, value = next(iter(command.items()))
    valid = ((key == "mode" and value in MODES)
             or (key == "fallback_mode" and value in FALLBACK_MODES)
             or (key == "idle_sleep" and value in (0, 1))
             or (key == "tds_threshold" and 100 <= value <= 300))
    if not valid:
        raise ValueError("Unsupported setting or value")
    return dict(command)
