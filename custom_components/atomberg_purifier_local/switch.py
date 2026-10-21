"""Display sleep and the daily sleep schedule."""
from homeassistant.components.switch import SwitchEntity

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        PurifierSwitch(entry.runtime_data, "idle_sleep", "Display sleep"),
        PurifierSwitch(entry.runtime_data, "sleep_mode", "Sleep schedule"),
    ])


class PurifierSwitch(PurifierEntity, SwitchEntity):
    _attr_icon = "mdi:sleep"

    @property
    def is_on(self):
        return self.coordinator.data.settings[self.key] == 1

    async def _set(self, enabled):
        command = {self.key: int(enabled)}
        if self.key == "sleep_mode" and enabled:
            state = self.coordinator.data.settings
            command.update(start_utc=state["start_utc"], stop_utc=state["stop_utc"])
        await self.coordinator.command(command)

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)
