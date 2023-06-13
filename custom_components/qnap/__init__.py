"""The qnap component."""

from qnapstats import QNAPStats

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, DOMAIN
from .coordinator import QnapCoordinator
from homeassistant.exceptions import PlatformNotReady

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(hass, config_entry):
    """Set the config entry up."""
    hass.data.setdefault(DOMAIN, {})
    if not (coordinator := QnapCoordinator(hass, config_entry):
        raise PlatformNotReady
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok
