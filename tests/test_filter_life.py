"""App-derived capacities, using synthetic counters rather than recordings."""
import pytest

from helpers import DEVICE, wire
from purifier.protocol import FILTER_LIFE, State, decode_message


def test_all_eight_components_use_their_own_capacity_and_counter():
    _, state = decode_message(wire(changes={
        19: 6250000, 24: 2000000, 25: 3000000, 26: 5400000,
        27: 3600000, 40: 6250000, 44: 9375000,
    }))
    assert {key: state.filter_life(key) for key in FILTER_LIFE} == {
        "pre_filter_life": 75, "sediment_filter_life": 75,
        "pre_carbon_filter_life": 75, "ro_membrane_life": 25,
        "uf_membrane_life": 75, "uv_lamp_life": 75,
        "pump_life": 50, "alkaliser_life": 50,
    }


def test_new_device_uses_unscaled_flow_until_scaled_total_exceeds_100_litres():
    _, state = decode_message(wire(changes={24: 1250000, 25: 2500000,
                                           40: 100000, 44: 9000000}))
    assert state.filter_life("pre_filter_life") == 80
    assert state.filter_life("ro_membrane_life") == 90
    _, scaled = decode_message(wire(changes={24: 1250000, 25: 2500000,
                                            40: 100001, 44: 9375000}))
    assert scaled.filter_life("pre_filter_life") == 100
    assert scaled.filter_life("ro_membrane_life") == 25


def test_app_rounds_remaining_life_up_and_exhausted_capacity_stops_at_zero():
    _, state = decode_message(wire(changes={19: 1250001, 25: 1, 27: 7200001}))
    assert state.filter_life("alkaliser_life") == 90  # 89.999992%, not 89%.
    assert state.filter_life("uf_membrane_life") == 100
    assert state.filter_life("pump_life") == 0


@pytest.mark.parametrize("bad", ["nan", "inf", "-1", "invalid", "1000000000001"])
def test_invalid_filter_counter_keeps_other_readings_and_controls_working(bad):
    _, state = decode_message(wire(changes={40: bad}))
    assert state.filter_life("pre_filter_life") is None
    assert state.filter_life("ro_membrane_life") is None
    assert state.filter_life("pump_life") == 99
    assert state.settings["mode"] == 3
    assert state.lifetime_water == 1000


def test_unavailable_ro_counter_does_not_invent_a_healthy_membrane():
    _, state = decode_message(wire(changes={44: "invalid"}))
    assert state.filter_life("ro_membrane_life") is None
    assert state.filter_life("pre_filter_life") == 92
    missing = State(DEVICE, ())
    assert all(missing.filter_life(key) is None for key in FILTER_LIFE)


def test_drawing_water_does_not_use_up_filter_capacity_without_production():
    _, before = decode_message(wire(changes={29: 8000}))
    _, after = decode_message(wire(changes={29: 6500, 18: 0, 50: 1}))
    assert [before.filter_life(k) for k in FILTER_LIFE] == [after.filter_life(k) for k in FILTER_LIFE]
