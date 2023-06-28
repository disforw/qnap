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
    async_add_entities(sensors)



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
        if self.coordinator.data:
            data = self.coordinator.data["system_stats"]
            days = int(data["uptime"]["days"])
            hours = int(data["uptime"]["hours"])
            minutes = int(data["uptime"]["minutes"])

            return f"{days:0>2d}d {hours:0>2d}h {minutes:0>2d}m"


