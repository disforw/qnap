"""Support for QNAP NAS firmware update entity."""

from __future__ import annotations

from homeassistant.components.update import UpdateDeviceClass, UpdateEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QnapConfigEntry, QnapCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: QnapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up QNAP update entities."""
    coordinator = config_entry.runtime_data
    uid = config_entry.unique_id
    assert uid is not None
    async_add_entities([QNAPFirmwareUpdateEntity(coordinator, uid)])


class QNAPFirmwareUpdateEntity(CoordinatorEntity[QnapCoordinator], UpdateEntity):
    """Update entity for QNAP NAS firmware."""

    _attr_has_entity_name = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: QnapCoordinator, unique_id: str) -> None:
        """Initialize the QNAP firmware update entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{unique_id}_firmware_update"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            serial_number=unique_id,
            name=coordinator.data.system_info.name,
            model=coordinator.data.system_info.model,
            sw_version=coordinator.data.system_info.firmware_version,
            manufacturer="QNAP",
        )

    @property
    def installed_version(self) -> str | None:
        """Return the currently installed firmware version."""
        fw = self.coordinator.data.firmware_update
        return fw.current_version if fw else None

    @property
    def latest_version(self) -> str | None:
        """Return the latest available firmware version.

        Returns None when no update info is available or when firmware
        is up to date — HA treats None as up-to-date.
        """
        fw = self.coordinator.data.firmware_update
        if fw is None:
            return None
        return fw.latest_version
