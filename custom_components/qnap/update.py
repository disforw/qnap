"""Support for QNAP NAS update platform."""
from typing import Final

from homeassistant.components.update import UpdateEntity, UpdateEntityDescription, UpdateDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QnapCoordinator

UPDATE_ENTITIES = [
  UpdateEntityDescription(
    key="update",
  )
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    """Set up entry."""
    coordinator = QnapCoordinator(hass, config_entry)
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise PlatformNotReady
    uid = config_entry.unique_id
    assert uid is not None

    async_add_entities(
        QNAPUpdateEntity(coordinator, description, uid)
        for description in UPDATE_ENTITIES
    )


class QNAPUpdateEntity(CoordinatorEntity[QnapCoordinator], UpdateEntity):
    """Base class for a QNAP update entity."""
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_has_entity_name = True
    _attr_name = "Firmware"

    def __init__(
        self,
        coordinator: QnapCoordinator,
        description: UpdateEntityDescription,
        unique_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.device_name = self.coordinator.data["system_stats"]["system"]["name"]
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=self.device_name,
            model=self.coordinator.data["system_stats"]["system"]["model"],
            sw_version=self.coordinator.data["system_stats"]["firmware"]["version"],
            manufacturer="QNAP",
        )

    @property
    def installed_version(self) -> str | None:
        """Version currently in use."""
        return self.coordinator.data["system_stats"]["firmware"]["version"]

    @property
    def latest_version(self) -> str | None:
        """Version update available."""
        return self.coordinator.data["firmware"]
