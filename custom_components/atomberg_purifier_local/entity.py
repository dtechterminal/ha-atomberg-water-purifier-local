"""Shared device identity."""
from homeassistant.helpers.device_registry import DeviceInfo, CONNECTION_NETWORK_MAC
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class PurifierEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        device_id = coordinator.data.device_id
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{device_id}_{key}"
        mac = ":".join(device_id[i:i+2] for i in range(0, 12, 2))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)}, connections={(CONNECTION_NETWORK_MAC, mac)},
            name="Atomberg Water Purifier", manufacturer="Atomberg", model="Intellon (W2)",
            sw_version=coordinator.data.fields[4],
        )
