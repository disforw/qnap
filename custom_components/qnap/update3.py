"""Support for QNAP NAS update platform."""
from __future__ import annotations

from typing import Final

from yarl import URL

from homeassistant.components.update import UpdateEntity, UpdateEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
)
from .coordinator import QnapCoordinator

UPDATE_ENTITIES: Final = [
  UpdateEntityDescription(
    key="update",
    name="Update",
    entity_category=EntityCategory.DIAGNOSTIC,
  )
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator = QnapCoordinator(hass, config_entry)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise PlatformNotReady
    uid = config_entry.unique_id
    assert uid is not None
    sensors: list[QNAPSensor] = []

    sensors.extend(
        [
            QNAPSystemSensor(coordinator, description, uid)
            for description in _SYSTEM_MON_COND
        ]
    )

    async_add_entities(sensors)


class QNAPUpdateEntity(CoordinatorEntity[QnapCoordinator], UpdateEntity):
    """Base class for a QNAP update entity."""

    def __init__(
        self,
        coordinator: QnapCoordinator,
        description: UpdateEntityDescription,
        unique_id: str,
        monitor_device: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.device_name = self.coordinator.data["system_stats"]["system"]["name"]
        self.monitor_device = monitor_device
        self._attr_unique_id = f"{unique_id}_{description.key}"
        if monitor_device:
            self._attr_unique_id = f"{self._attr_unique_id}_{monitor_device}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=self.device_name,
            model=self.coordinator.data["system_stats"]["system"]["model"],
            sw_version=self.coordinator.data["system_stats"]["firmware"]["version"],
            manufacturer="QNAP",
        )
