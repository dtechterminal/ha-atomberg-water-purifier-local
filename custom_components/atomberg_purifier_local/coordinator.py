"""Poll state and publish only confirmed changes."""
from datetime import timedelta
import logging

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .client import CannotConnect, LocalClient
from .protocol import State

_LOGGER = logging.getLogger(__name__)


class PurifierCoordinator(DataUpdateCoordinator[State]):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name="Atomberg purifier", config_entry=entry,
                         update_interval=timedelta(seconds=10))
        self.client = LocalClient(entry.data["host"], entry.unique_id)
        self.last_successful_read = None

    async def _async_update_data(self) -> State:
        try:
            state = await self.client.read()
            self.last_successful_read = dt_util.utcnow()
            return state
        except (CannotConnect, ValueError) as err:
            raise UpdateFailed(str(err)) from err

    async def command(self, command: dict) -> None:
        try:
            state = await self.client.exchange(command)
        except (CannotConnect, ValueError) as err:
            raise HomeAssistantError(str(err)) from err
        self.last_successful_read = dt_util.utcnow()
        self.async_set_updated_data(state)
