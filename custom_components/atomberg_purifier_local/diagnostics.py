"""Export local measurements for mapping additional W2 sensors.

Do not include config entry data, device IDs, MACs or network addresses.
"""


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    state = coordinator.data
    return {
        "last_update_success": coordinator.last_update_success,
        "receiver": coordinator.client.receiver,
        "model": state.fields[2],
        "firmware": state.fields[4],
        "settings": state.settings,
        "field_index_base": 0,
        "state_fields": dict(enumerate(state.fields)),
    }
