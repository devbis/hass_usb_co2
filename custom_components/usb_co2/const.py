import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "usb_co2"
PLATFORMS: Final = [Platform.SENSOR]

LOGGER = logging.getLogger(__package__)
