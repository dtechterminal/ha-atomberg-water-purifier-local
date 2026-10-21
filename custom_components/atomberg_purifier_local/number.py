"""Adaptive treatment threshold."""
from homeassistant.components.number import NumberEntity, NumberMode

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([PurifierThreshold(entry.runtime_data, "tds_threshold", "TDS threshold")])


class PurifierThreshold(PurifierEntity, NumberEntity):
    _attr_native_min_value = 100
    _attr_native_max_value = 300
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "ppm"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:water-check"

    @property
    def native_value(self):
        return self.coordinator.data.settings["tds_threshold"]

    async def async_set_native_value(self, value):
        if value != int(value):
            raise ValueError("The TDS threshold must be a whole number")
        await self.coordinator.command({"tds_threshold": int(value)})
