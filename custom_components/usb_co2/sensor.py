"""CO2 Sensors."""

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, ENTITY_ID_FORMAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import co2meter as co2

from .const import DOMAIN, LOGGER
from .coordinator import UsbCo2DataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entities based on a config entry."""
    coordinator = UsbCo2DataCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([CarbonDioxideEntity(coordinator), TemperatureEntity(coordinator)])


class UsbCo2DataEntity(CoordinatorEntity):
    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.dev_id)},
            manufacturer= self.coordinator.co2_dev.info['manufacturer'],
            sw_version=self.coordinator.co2_dev.info["serial_no"],
            model=self.coordinator.dev_id,
        )


class CarbonDioxideEntity(UsbCo2DataEntity, SensorEntity):
    """Defines a CO2 sensor."""

    _attr_device_class = SensorDeviceClass.CO2
    _attr_icon = "mdi:molecule-co2"
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self._attr_name = f'Carbon Dioxide'
        self._attr_unique_id = f"{self.coordinator.dev_id}_co2"
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self._attr_unique_id, hass=self.coordinator.hass)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data['co2']
        self.async_write_ha_state()

class TemperatureEntity(UsbCo2DataEntity, SensorEntity):
    """Defines a Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self._attr_name = f'Temperature'
        self._attr_unique_id = f"{self.coordinator.dev_id}_temperature"
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self._attr_unique_id, hass=self.coordinator.hass)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data['temperature']
        self.async_write_ha_state()
