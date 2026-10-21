"""Daily sleep times, displayed in Home Assistant's configured time zone."""
from homeassistant.components.time import TimeEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        PurifierTime(entry.runtime_data, "start_utc", "Sleep start"),
        PurifierTime(entry.runtime_data, "stop_utc", "Sleep end"),
    ])


class PurifierTime(PurifierEntity, TimeEntity):
    @property
    def native_value(self):
        seconds = self.coordinator.data.settings[self.key] % 86400
        today = dt_util.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        return dt_util.as_local(today + timedelta(seconds=seconds)).time().replace(tzinfo=None)

    async def async_set_value(self, value):
        state = self.coordinator.data.settings
        if not state["sleep_mode"]:
            raise HomeAssistantError("Turn on Sleep schedule before changing its times.")
        local = dt_util.now().replace(hour=value.hour, minute=value.minute, second=value.second,
                                     microsecond=0)
        command = {"sleep_mode": 1, "start_utc": state["start_utc"], "stop_utc": state["stop_utc"]}
        command[self.key] = int(dt_util.as_utc(local).timestamp())
        await self.coordinator.command(command)
