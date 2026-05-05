"""Support for QNAP NAS Sensors."""

from __future__ import annotations

import logging

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
        key="cpu_temp",
        translation_key="cpu_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
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
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        icon="mdi:memory",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_used",
        translation_key="memory_used",
        native_unit_of_measurement=UnitOfInformation.GIBIBYTES,
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
        key="network_link_status",
        translation_key="network_link_status",
        icon="mdi:checkbox-marked-circle-outline",
    ),
    SensorEntityDescription(
        key="network_tx",
        translation_key="network_tx",
        native_unit_of_measurement=UnitOfDataRate.MEBIBYTES_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="network_rx",
        translation_key="network_rx",
        native_unit_of_measurement=UnitOfDataRate.MEBIBYTES_PER_SECOND,
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
    """Round a number based on its size (so it looks nice)."""
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
        QNAPNetworkSensor(coordinator, description, uid, nic)
        for nic in coordinator.data["system_stats"]["nics"]
        for description in _NETWORK_MON_COND
    )
    sensors.extend(
        QNAPDriveSensor(coordinator, description, uid, drive)
        for drive in coordinator.data["smart_drive_health"]
        for description in _DRIVE_MON_COND
    )
    sensors.extend(
        QNAPVolumeSensor(coordinator, description, uid, volume)
        for volume in coordinator.data["volumes"]
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
        monitor_device: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.monitor_device = monitor_device
        self._attr_unique_id = f"{unique_id}_{description.key}"
        if monitor_device:
            self._attr_unique_id = f"{self._attr_unique_id}_{monitor_device}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=coordinator.data["system_stats"]["system"]["name"],
            model=coordinator.data["system_stats"]["system"]["model"],
            sw_version=coordinator.data["system_stats"]["firmware"]["version"],
            manufacturer="QNAP",
        )


class QNAPCPUSensor(QNAPSensor):
    """A QNAP sensor that monitors CPU stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "cpu_temp":
            return self.coordinator.data["system_stats"]["cpu"]["temp_c"]
        if self.entity_description.key == "cpu_usage":
            return self.coordinator.data["system_stats"]["cpu"]["usage_percent"]
        return None


class QNAPMemorySensor(QNAPSensor):
    """A QNAP sensor that monitors memory stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        free = float(self.coordinator.data["system_stats"]["memory"]["free"]) / 1024
        if self.entity_description.key == "memory_free":
            return round_nicely(free)

        total = float(self.coordinator.data["system_stats"]["memory"]["total"]) / 1024
        used = total - free

        if self.entity_description.key == "memory_used":
            return round_nicely(used)
        if self.entity_description.key == "memory_percent_used":
            return round(used / total * 100)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data["system_stats"]["memory"]
            size = round_nicely(float(data["total"]) / 1024)
            return {ATTR_MEMORY_SIZE: f"{size} {UnitOfInformation.GIBIBYTES}"}
        return None


class QNAPNetworkSensor(QNAPSensor):
    """A QNAP sensor that monitors network stats."""

    @property
    def native_value(self) -> str | float | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "network_link_status":
            nic = self.coordinator.data["system_stats"]["nics"].get(self.monitor_device)
            if nic is None:
                return None
            return nic["link_status"]

        data = self.coordinator.data["bandwidth"].get(self.monitor_device)
        if data is None:
            return None

        if self.entity_description.key == "network_tx":
            return round_nicely(data["tx"] / 1024 / 1024)
        if self.entity_description.key == "network_rx":
            return round_nicely(data["rx"] / 1024 / 1024)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int] | None:
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data["system_stats"]["nics"].get(self.monitor_device)
            if data is None:
                return None
            return {
                ATTR_IP: data["ip"],
                ATTR_MASK: data["mask"],
                ATTR_MAC: data["mac"],
                ATTR_MAX_SPEED: data["max_speed"],
                ATTR_PACKETS_TX: data["tx_packets"],
                ATTR_PACKETS_RX: data["rx_packets"],
                ATTR_PACKETS_ERR: data["err_packets"],
            }
        return None


class QNAPSystemSensor(QNAPSensor):
    """A QNAP sensor that monitors overall system health."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        if self.entity_description.key == "status":
            return self.coordinator.data["system_health"]
        if self.entity_description.key == "system_temp":
            return int(self.coordinator.data["system_stats"]["system"]["temp_c"])
        return None


class QNAPDriveSensor(QNAPSensor):
    """A QNAP sensor that monitors HDD/SSD drive stats."""

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        data = self.coordinator.data["smart_drive_health"].get(self.monitor_device)
        if data is None:
            return None

        if self.entity_description.key == "drive_smart_status":
            return data["health"]
        if self.entity_description.key == "drive_temp":
            return int(data["temp_c"]) if data["temp_c"] is not None else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data["smart_drive_health"].get(self.monitor_device)
            if data is None:
                return None
            return {
                ATTR_DRIVE: data["drive_number"],
                ATTR_MODEL: data["model"],
                ATTR_SERIAL: data["serial"],
                ATTR_TYPE: data["type"],
            }
        return None


class QNAPVolumeSensor(QNAPSensor):
    """A QNAP sensor that monitors storage volume stats."""

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        data = self.coordinator.data["volumes"].get(self.monitor_device)
        if data is None:
            return None

        free_gb = int(data["free_size"]) / 1024 / 1024 / 1024
        if self.entity_description.key == "volume_size_free":
            return round_nicely(free_gb)

        total_gb = int(data["total_size"]) / 1024 / 1024 / 1024
        used_gb = total_gb - free_gb

        if self.entity_description.key == "volume_size_used":
            return round_nicely(used_gb)
        if self.entity_description.key == "volume_percentage_used":
            return round(used_gb / total_gb * 100)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data["volumes"].get(self.monitor_device)
            if data is None:
                return None
            total_gb = int(data["total_size"]) / 1024 / 1024 / 1024
            return {
                ATTR_VOLUME_SIZE: f"{round_nicely(total_gb)} {UnitOfInformation.GIBIBYTES}"
            }
        return None
