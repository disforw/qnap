"""Data coordinator for the qnap integration."""

from __future__ import annotations

from contextlib import contextmanager, nullcontext
from datetime import timedelta
import logging
from typing import Any
import warnings

from qnapstats import QNAPStats
import urllib3

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_PORT, DEFAULT_SSL, DEFAULT_TIMEOUT, DEFAULT_VERIFY_SSL, DOMAIN
from .container_station import ContainerStationClient

type QnapConfigEntry = ConfigEntry[QnapCoordinator]

UPDATE_INTERVAL = timedelta(minutes=1)

_LOGGER = logging.getLogger(__name__)


@contextmanager
def suppress_insecure_request_warning():
    """Context manager to suppress InsecureRequestWarning.

    Was added in here to solve the following issue, not being solved upstream.
    https://github.com/colinodell/python-qnapstats/issues/96
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
        yield


class QnapCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Custom coordinator for the qnap integration."""

    config_entry: QnapConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: QnapConfigEntry) -> None:
        """Initialize the qnap coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        protocol = "https" if config_entry.data[CONF_SSL] else "http"
        self._verify_ssl = config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        host = config_entry.data.get(CONF_HOST)
        port = config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        username = config_entry.data.get(CONF_USERNAME)
        password = config_entry.data.get(CONF_PASSWORD)
        ssl = config_entry.data.get(CONF_SSL, DEFAULT_SSL)
        timeout = config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        self._api = QNAPStats(
            f"{protocol}://{host}",
            port,
            username,
            password,
            verify_ssl=self._verify_ssl,
            timeout=timeout,
        )

        self.cs = ContainerStationClient(
            host=host,
            port=port,
            username=username,
            password=password,
            ssl=ssl,
            verify_ssl=self._verify_ssl,
            timeout=timeout,
        )

    def _sync_update(self) -> dict[str, Any]:
        """Get the latest data from the Qnap API."""
        with (
            suppress_insecure_request_warning()
            if not self._verify_ssl
            else nullcontext()
        ):
            data: dict[str, Any] = {
                "system_stats": self._api.get_system_stats(),
                "system_health": self._api.get_system_health(),
                "smart_drive_health": self._api.get_smart_disk_health(),
                "volumes": self._api.get_volumes(),
                "bandwidth": self._api.get_bandwidth(),
            }

            # Firmware update check — fetched separately; a malformed or
            # unexpected NAS API response should not fail the entire coordinator.
            try:
                data["firmware_update"] = self._api.get_firmware_update()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Firmware update check failed (non-fatal): %s", err)
                data["firmware_update"] = None

        # Container Station — fetched independently; failures are non-fatal
        try:
            # Reuse the QTS SID already obtained by qnapstats as Bearer token
            sid = self._api._sid  # noqa: SLF001
            if sid:
                data["containers"] = self.cs.get_containers(sid)
            else:
                _LOGGER.debug("QTS SID not yet available, skipping Container Station poll")
                data["containers"] = data.get("containers", [])
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Container Station unavailable: %s", err)
            data["containers"] = data.get("containers", [])

        return data

    async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the Qnap API."""
        return await self.hass.async_add_executor_job(self._sync_update)
