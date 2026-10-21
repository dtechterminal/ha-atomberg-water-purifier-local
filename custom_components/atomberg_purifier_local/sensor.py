"""Verified water-quality readings and connection diagnostics."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ConnectionSensor(entry.runtime_data, "connection", "Connection"),
        InputTdsSensor(entry.runtime_data, "input_tds", "Input TDS"),
        OutputTdsSensor(entry.runtime_data, "output_tds", "Output TDS"),
    ])


class InputTdsSensor(PurifierEntity, SensorEntity):
    _attr_native_unit_of_measurement = "mg/L"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:water"

    @property
    def native_value(self):
        return float(self.coordinator.data.fields[6])


class OutputTdsSensor(InputTdsSensor):
    @property
    def native_value(self):
        # Matches app output at 100 mg/L (99.78) and 91 mg/L (90.70).
        return float(self.coordinator.data.fields[41])


class ConnectionSensor(PurifierEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:lan-connect"

    @property
    def native_value(self):
        return "Local network"

    @property
    def extra_state_attributes(self):
        return {"receiver": self.coordinator.client.receiver}
