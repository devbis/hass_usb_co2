from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

import co2meter as co2

from .const import LOGGER


class UsbCo2DataCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, config_entry) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            config_entry=config_entry,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )
        self.co2_dev: co2.CO2monitor | None = None
        self.dev_id: str = ''

    async def _async_setup(self):
        """Set up the coordinator

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        self.co2_dev = co2.CO2monitor(False)
        self.dev_id = f'{self.co2_dev.info["product_name"]}_{self.co2_dev.info["serial_no"].replace(".", "_")}'

    # async def update_method(self):
    async def _async_update_data(self):
        dt, co2_ppm, temp = self.co2_dev.read_data_raw()
        if co2_ppm is None and temp is None:
            LOGGER.warning(
                f"Fallback to read with bypass_decrypt={not self.co2_dev.bypass_decrypt}",
            )
            self.co2_dev.bypass_decrypt = not self.co2_dev.bypass_decrypt
            dt, co2_ppm, temp = self.co2_dev.read_data_raw()
        return {'co2': co2_ppm, 'temperature': temp}
