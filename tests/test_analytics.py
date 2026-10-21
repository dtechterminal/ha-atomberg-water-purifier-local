"""Counter conversion and invalid-reading handling, using synthetic states."""
import pytest

from helpers import DEVICE, wire
from purifier.protocol import State, decode_message


def test_analytics_use_device_totals_not_tank_level_or_current_flow():
    _, state = decode_message(wire(changes={19: 1250500, 24: 1100000, 25: 150000,
                                           26: 151200, 27: 120000, 29: 8000}))
    assert state.lifetime_water == 1250.5
    assert state.water_saved == 2100
    assert state.runtime == 42
    _, drawn = decode_message(wire(changes={19: 1250500, 24: 1100000, 25: 150000,
                                           26: 151200, 27: 120000, 29: 7000}))
    assert drawn.lifetime_water == state.lifetime_water
    assert drawn.water_saved == state.water_saved
    assert drawn.runtime == state.runtime


def test_production_delta_and_fractional_runtime_are_preserved():
    _, before = decode_message(wire(changes={19: 1250500, 24: 1100000, 25: 150000,
                                            26: 151200}))
    _, after = decode_message(wire(changes={19: 1251200, 24: 1100600, 25: 150100,
                                           26: 151260}))
    assert after.lifetime_water - before.lifetime_water == pytest.approx(.7)
    assert after.water_saved - before.water_saved == pytest.approx(1.2)
    assert after.runtime - before.runtime == pytest.approx(1 / 60)


@pytest.mark.parametrize('value', ['-1', 'nan', 'inf', 'not-a-number', '1000000000001'])
def test_bad_analytics_do_not_report_zero_or_a_fabricated_total(value):
    _, state = decode_message(wire(changes={19: value, 24: value, 26: value}))
    assert state.lifetime_water is None
    assert state.water_saved is None
    assert state.runtime is None
    assert state.settings['mode'] == 3


def test_missing_counter_is_unknown():
    state = State(DEVICE, ('0',) * 19)
    assert state.lifetime_water is None
    assert state.water_saved is None
    assert state.runtime is None
