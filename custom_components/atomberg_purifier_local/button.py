"""Refresh device readings immediately over the local network."""
from homeassistant.components.button import ButtonEntity

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        RefreshButton(entry.runtime_data, "refresh_readings", "Refresh readings"),
    ])


class RefreshButton(PurifierEntity, ButtonEntity):
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        await self.coordinator.command({"read": 1})
