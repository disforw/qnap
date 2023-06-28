"""Support for QNAP NAS Sensors."""
from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_NAME,
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import QnapCoordinator

_LOGGER = logging.getLogger(__name__)


_SYS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:checkbox-marked-circle-outline",
    ),
    SensorEntityDescription(
        key="system_temp",
        name="System Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


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
    sensors: list[QNAPSensor] = []

    sensors.extend(
        [
            QNAPSystemSensor(coordinator, description, uid)
            for description in _SYS_SENSORS
        ]
    )

    sensors.extend(
        [QNAPCPUSensor(coordinator, description, uid) for description in _CPU_SENSORS]
    )

    sensors.extend(
        [
            QNAPMemorySensor(coordinator, description, uid)
            for description in _MEM_SENSORS
        ]
    )

    # Network sensors
    sensors.extend(
        [
            QNAPNetworkSensor(coordinator, description, uid, nic)
            for nic in coordinator.data["system_stats"]["nics"]
            for description in _NET_SENSORS
        ]
    )

    # Drive sensors
    sensors.extend(
        [
            QNAPDriveSensor(coordinator, description, uid, drive)
            for drive in coordinator.data["smart_drive_health"]
            for description in _DRI_SENSORS
        ]
    )

    # Volume sensors
    sensors.extend(
        [
            QNAPVolumeSensor(coordinator, description, uid, volume)
            for volume in coordinator.data["volumes"]
            for description in _VOL_SENSORS
        ]
    )
    async_add_entities(sensors)


def round_nicely(number):
    """Round a number based on its size (so it looks nice)."""
    if number < 10:
        return round(number, 2)
    if number < 100:
        return round(number, 1)

    return round(number)


class QNAPSensor(CoordinatorEntity[QnapCoordinator], SensorEntity):
    """Base class for a QNAP sensor."""

    def __init__(
        self,
        coordinator: QnapCoordinator,
        description,
        uid,
        monitor_device: str | None = None,
        monitor_subdevice: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = description
        self.uid = uid
        self.device_name = self.coordinator.data["system_stats"]["system"]["name"]
        self.monitor_device = monitor_device
        self.monitor_subdevice = monitor_subdevice
        self.coordinator_context=None
        self._attr_unique_id = f"{self.uid}_{self.device_name}_{self.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.uid)},
            name=self.device_name,
            model=self.coordinator.data["system_stats"]["system"]["model"],
            sw_version=self.coordinator.data["system_stats"]["firmware"]["version"],
            manufacturer=DEFAULT_NAME,
        )

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self.monitor_device is not None:
            return f"{self.device_name} {self.entity_description.name} ({self.monitor_device})"
        return f"{self.device_name} {self.entity_description.name}"


class QNAPSystemTime(QNAPSensor):
    """A QNAP sensor that monitors overall system health."""

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.entity_description.key == "status":
            return self.coordinator.data["system_health"]

        if self.entity_description.key == "system_temp":
            return int(self.coordinator.data["system_stats"]["system"]["temp_c"])

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data["system_stats"]
            days = int(data["uptime"]["days"])
            hours = int(data["uptime"]["hours"])
            minutes = int(data["uptime"]["minutes"])

            return {
                ATTR_NAME: data["system"]["name"],
                ATTR_MODEL: data["system"]["model"],
                ATTR_SERIAL: data["system"]["serial_number"],
                ATTR_UPTIME: f"{days:0>2d}d {hours:0>2d}h {minutes:0>2d}m",
            }


