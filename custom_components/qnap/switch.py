"""Support for QNAP Container Station switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QnapConfigEntry, QnapCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: QnapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up QNAP Container Station switch entities."""
    coordinator = config_entry.runtime_data
    uid = config_entry.unique_id
    assert uid is not None

    # Build initial set of switches from first coordinator data
    containers: list[dict[str, Any]] = coordinator.data.get("containers", [])
    async_add_entities(
        QNAPContainerSwitch(coordinator, uid, container)
        for container in containers
    )


class QNAPContainerSwitch(CoordinatorEntity[QnapCoordinator], SwitchEntity):
    """A switch entity representing a Container Station container.

    Turns on = running, turns off = stopped.
    """

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: QnapCoordinator,
        unique_id: str,
        container: dict[str, Any],
    ) -> None:
        """Initialize the container switch."""
        super().__init__(coordinator)
        self._container_name = container["name"]
        self._container_id = container["id"]
        self._container_type = container.get("type", "docker")

        self._attr_unique_id = f"{unique_id}_container_{self._container_name}"
        self._attr_name = self._container_name
        self._attr_icon = "mdi:docker"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def _get_container_data(self) -> dict[str, Any] | None:
        """Return current data for this container from coordinator."""
        for c in self.coordinator.data.get("containers", []):
            if c["name"] == self._container_name:
                return c
        return None

    @property
    def is_on(self) -> bool | None:
        """Return True if container is running."""
        container = self._get_container_data()
        if container is None:
            return None
        return container["status"] == "running"

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return container image and type as extra attributes."""
        container = self._get_container_data()
        if container is None:
            return None
        return {
            "image": container.get("image", ""),
            "container_type": container.get("type", "docker"),
            "container_id": container.get("id", "")[:12],
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the container."""
        await self.hass.async_add_executor_job(
            self.coordinator.cs.container_action,
            self._container_id,
            self._container_type,
            "start",
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the container."""
        await self.hass.async_add_executor_job(
            self.coordinator.cs.container_action,
            self._container_id,
            self._container_type,
            "stop",
        )
        await self.coordinator.async_request_refresh()
