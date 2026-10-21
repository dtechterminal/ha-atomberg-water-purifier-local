"""Verified water-quality readings and connection diagnostics."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory

from .entity import PurifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ConnectionSensor(entry.runtime_data, "connection", "Connection"),
        InputTdsSensor(entry.runtime_data, "input_tds", "Input TDS"),
        OutputTdsSensor(entry.runtime_data, "output_tds", "Output TDS"),
        AnalyticsSensor(entry.runtime_data, "lifetime_water", "Lifetime water", "L",
                        SensorDeviceClass.WATER, "mdi:water"),
        AnalyticsSensor(entry.runtime_data, "water_saved", "Water saved", "L",
                        SensorDeviceClass.VOLUME, "mdi:water-check"),
        AnalyticsSensor(entry.runtime_data, "runtime", "Runtime", "h",
                        SensorDeviceClass.DURATION, "mdi:timer-outline"),
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


class AnalyticsSensor(PurifierEntity, SensorEntity):
    """App-cross-checked W2 analytics, pending a complete refill comparison.

    Deliberately omit a statistics state class until counter/reset semantics
    have been validated. Recorder history remains available.
    """

    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, key, name, unit, device_class, icon):
        super().__init__(coordinator, key, name)
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self.key)

    @property
    def extra_state_attributes(self):
        return {
            "mapping_status": "beta",
            "validation": "Matched against W2 app; refill-cycle validation pending",
        }
