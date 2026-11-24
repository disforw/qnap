"""Diagnostics support for the QNAP integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import QnapConfigEntry

TO_REDACT = {
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    "ip",
    "mac",
    "serial_number",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: QnapConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    # entry.runtime_data is only set once the coordinator's first refresh
    # succeeds, so a failed/incomplete setup leaves it unset.
    coordinator = getattr(entry, "runtime_data", None)

    data: dict[str, Any] | None = None
    last_update_success: bool | None = None
    if coordinator is not None:
        last_update_success = coordinator.last_update_success
        if coordinator.data is not None:
            data = async_redact_data(asdict(coordinator.data), TO_REDACT)

    return {
        "entry": {
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
        },
        "last_update_success": last_update_success,
        "data": data,
    }
