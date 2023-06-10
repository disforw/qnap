"""Data coordinator for the dwd_weather_warnings integration."""

from __future__ import annotations

from dwdwfsapi import DwdWeatherWarningsAPI

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class DwdWeatherWarningsCoordinator(DataUpdateCoordinator[None]):
    """Custom coordinator for the dwd_weather_warnings integration."""

    def __init__(self, hass: HomeAssistant, api: DwdWeatherWarningsAPI) -> None:
        """Initialize the dwd_weather_warnings coordinator."""
        super().__init__(
            hass, LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL
        )

        self.api = api

    async def _async_update_data(self) -> None:
        """Get the latest data from the DWD Weather Warnings API."""
        await self.hass.async_add_executor_job(self.api.update)
-----
        
async def async_update_data():
        datas = {}
        datas["system_stats"] = await hass.async_add_executor_job(api.get_system_stats)
        datas["system_health"] = await hass.async_add_executor_job(
            api.get_system_health
        )
        datas["smart_drive_health"] = await hass.async_add_executor_job(
            api.get_smart_disk_health
        )
        datas["volumes"] = await hass.async_add_executor_job(api.get_volumes)
        datas["bandwidth"] = await hass.async_add_executor_job(api.get_bandwidth)
        return datas

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

