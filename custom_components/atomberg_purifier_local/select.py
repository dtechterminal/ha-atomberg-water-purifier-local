"""Purification and fallback modes."""
from homeassistant.components.select import SelectEntity

from .entity import PurifierEntity
from .protocol import MODES, FALLBACK_MODES


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        PurifierSelect(entry.runtime_data, "mode", "Purification mode", MODES),
        PurifierSelect(entry.runtime_data, "fallback_mode", "Fallback mode", FALLBACK_MODES),
    ])


class PurifierSelect(PurifierEntity, SelectEntity):
    _attr_icon = "mdi:water-sync"

    def __init__(self, coordinator, key, name, choices):
        super().__init__(coordinator, key, name)
        self.choices = choices
        self._attr_options = list(choices.values())

    @property
    def current_option(self):
        return self.choices.get(self.coordinator.data.settings[self.key])

    async def async_select_option(self, option):
        value = next(key for key, name in self.choices.items() if name == option)
        await self.coordinator.command({self.key: value})
