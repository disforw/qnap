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

    async_add_entities(
        QNAPContainerSwitch(
            coordinator, uid, container.name, container.id, container.type
        )
        for container in coordinator.data.containers
    )


class QNAPContainerSwitch(CoordinatorEntity[QnapCoordinator], SwitchEntity):
    """A switch entity representing a Container Station container."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: QnapCoordinator,
        unique_id: str,
        container_name: str,
        container_id: str,
        container_type: str,
    ) -> None:
        """Initialize the container switch."""
        super().__init__(coordinator)
        self._container_name = container_name
        self._container_id = container_id
        self._container_type = container_type

        self._attr_unique_id = f"{unique_id}_container_{container_name}"
        self._attr_name = container_name
        self._attr_icon = "mdi:docker"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, unique_id)})

    def _get_container(self):
        """Return current container data from coordinator."""
        return next(
            (
                c
                for c in self.coordinator.data.containers
                if c.name == self._container_name
            ),
            None,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if container is running."""
        container = self._get_container()
        if container is None:
            return None
        return container.state == "running"

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return container image and type as extra attributes."""
        container = self._get_container()
        if container is None:
            return None
        return {
            "image": container.image,
            "container_type": container.type,
            "container_id": container.id[:12],
            "state": container.state,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the container."""
        await self.coordinator._cs.start_container(
            self._container_id, self._container_type
        )  # noqa: SLF001
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the container."""
        await self.coordinator._cs.stop_container(
            self._container_id, self._container_type
        )  # noqa: SLF001
        await self.coordinator.async_request_refresh()
