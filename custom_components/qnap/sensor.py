"""Support for QNAP NAS Sensors."""

from __future__ import annotations

import logging

from qnap_client.models import NasData

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QnapConfigEntry, QnapCoordinator

_LOGGER = logging.getLogger(__name__)

ATTR_DRIVE = "Drive"
ATTR_IP = "IP Address"
ATTR_MAC = "MAC Address"
ATTR_MASK = "Mask"
ATTR_MAX_SPEED = "Max Speed"
ATTR_MEMORY_SIZE = "Memory Size"
ATTR_MODEL = "Model"
ATTR_PACKETS_TX = "Packets (TX)"
ATTR_PACKETS_RX = "Packets (RX)"
ATTR_PACKETS_ERR = "Packets (Err)"
ATTR_SERIAL = "Serial #"
ATTR_TYPE = "Type"
ATTR_VOLUME_SIZE = "Volume Size"

_SYSTEM_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:checkbox-marked-circle-outline",
    ),
    SensorEntityDescription(
        key="system_temp",
        translation_key="system_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_CPU_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:chip",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_MEMORY_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="memory_free",
        translation_key="memory_free",
        native_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:memory",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_used",
        translation_key="memory_used",
        native_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:memory",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_percent_used",
        translation_key="memory_percent_used",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_NETWORK_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="network_tx",
        translation_key="network_tx",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="network_rx",
        translation_key="network_rx",
        native_unit_of_measurement=UnitOfDataRate.MEGABYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_DRIVE_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="drive_smart_status",
        translation_key="drive_smart_status",
        icon="mdi:checkbox-marked-circle-outline",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="drive_temp",
        translation_key="drive_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_VOLUME_MON_COND: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="volume_size_used",
        translation_key="volume_size_used",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:chart-pie",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="volume_size_free",
        translation_key="volume_size_free",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:chart-pie",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="volume_percentage_used",
        translation_key="volume_percentage_used",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:chart-pie",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


def round_nicely(number: float) -> float:
    """Round a number based on its size."""
    if number < 10:
        return round(number, 2)
    if number < 100:
        return round(number, 1)
    return round(number)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: QnapConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    coordinator = config_entry.runtime_data
    uid = config_entry.unique_id
    assert uid is not None
    data: NasData = coordinator.data

    sensors: list[QNAPSensor] = []

    sensors.extend(
        QNAPSystemSensor(coordinator, description, uid)
        for description in _SYSTEM_MON_COND
    )
    sensors.extend(
        QNAPCPUSensor(coordinator, description, uid)
        for description in _CPU_MON_COND
    )
    sensors.extend(
        QNAPMemorySensor(coordinator, description, uid)
        for description in _MEMORY_MON_COND
    )
    sensors.extend(
        QNAPNetworkSensor(coordinator, description, uid, iface.name)
        for iface in data.network_interfaces
        for description in _NETWORK_MON_COND
    )
    sensors.extend(
        QNAPDriveSensor(coordinator, description, uid, drive.drive_number)
        for drive in data.drive_health
        for description in _DRIVE_MON_COND
    )
    sensors.extend(
        QNAPVolumeSensor(coordinator, description, uid, vol.name)
        for vol in data.volumes
        for description in _VOLUME_MON_COND
    )
    async_add_entities(sensors)


class QNAPSensor(CoordinatorEntity[QnapCoordinator], SensorEntity):
    """Base class for a QNAP sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: QnapCoordinator,
        description: SensorEntityDescription,
        unique_id: str,
        monitor_device: str | int | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.monitor_device = monitor_device
        self._attr_unique_id = f"{unique_id}_{description.key}"
        if monitor_device is not None:
            self._attr_unique_id = f"{self._attr_unique_id}_{monitor_device}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=coordinator.data.system_info.name,
            model=coordinator.data.system_info.model,
            sw_version=coordinator.data.system_info.firmware_version,
            manufacturer="QNAP",
        )


class QNAPCPUSensor(QNAPSensor):
    """A QNAP sensor that monitors CPU stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "cpu_usage":
            return round(self.coordinator.data.system_info.cpu_usage_percent, 1)
        return None


class QNAPMemorySensor(QNAPSensor):
    """A QNAP sensor that monitors memory stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        info = self.coordinator.data.system_info
        if self.entity_description.key == "memory_free":
            return info.memory_free_mb
        if self.entity_description.key == "memory_used":
            return info.memory_used_mb
        if self.entity_description.key == "memory_percent_used":
            if info.memory_total_mb == 0:
                return None
            return round(info.memory_used_mb / info.memory_total_mb * 100)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        total = self.coordinator.data.system_info.memory_total_mb
        return {ATTR_MEMORY_SIZE: f"{total} {UnitOfInformation.MEBIBYTES}"}


class QNAPNetworkSensor(QNAPSensor):
    """A QNAP sensor that monitors network stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        iface = next(
            (i for i in self.coordinator.data.network_interfaces if i.name == self.monitor_device),
            None,
        )
        if iface is None:
            return None
        if self.entity_description.key == "network_tx":
            return round_nicely(iface.tx_bytes_per_sec / 1024 / 1024)
        if self.entity_description.key == "network_rx":
            return round_nicely(iface.rx_bytes_per_sec / 1024 / 1024)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        iface = next(
            (i for i in self.coordinator.data.network_interfaces if i.name == self.monitor_device),
            None,
        )
        if iface is None:
            return None
        return {
            ATTR_IP: iface.ip,
            ATTR_MAC: iface.mac,
        }


class QNAPSystemSensor(QNAPSensor):
    """A QNAP sensor that monitors overall system health."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "status":
            return self.coordinator.data.system_health.status
        if self.entity_description.key == "system_temp":
            # system_temp not directly in NasData — not available from qnap_client yet
            return None
        return None


class QNAPDriveSensor(QNAPSensor):
    """A QNAP sensor that monitors HDD/SSD drive stats."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        drive = next(
            (d for d in self.coordinator.data.drive_health if d.drive_number == self.monitor_device),
            None,
        )
        if drive is None:
            return None
        if self.entity_description.key == "drive_smart_status":
            return drive.health
        if self.entity_description.key == "drive_temp":
            return drive.temperature
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        drive = next(
            (d for d in self.coordinator.data.drive_health if d.drive_number == self.monitor_device),
            None,
        )
        if drive is None:
            return None
        return {
            ATTR_DRIVE: str(drive.drive_number),
            ATTR_MODEL: drive.model,
            ATTR_TYPE: "HDD/SSD",
        }


class QNAPVolumeSensor(QNAPSensor):
    """A QNAP sensor that monitors storage volume stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        vol = next(
            (v for v in self.coordinator.data.volumes if v.name == self.monitor_device),
            None,
        )
        if vol is None:
            return None

        if self.entity_description.key == "volume_size_free":
            return round_nicely(vol.free_bytes / 1024 / 1024 / 1024)
        if self.entity_description.key == "volume_size_used":
            return round_nicely(vol.used_bytes / 1024 / 1024 / 1024)
        if self.entity_description.key == "volume_percentage_used":
            if vol.total_bytes == 0:
                return None
            return round(vol.used_bytes / vol.total_bytes * 100)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        vol = next(
            (v for v in self.coordinator.data.volumes if v.name == self.monitor_device),
            None,
        )
        if vol is None:
            return None
        total_gb = round_nicely(vol.total_bytes / 1024 / 1024 / 1024)
        return {
            ATTR_VOLUME_SIZE: f"{total_gb} {UnitOfInformation.GIBIBYTES}",
        }
