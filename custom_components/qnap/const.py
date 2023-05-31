"""The Qnap constants."""
from __future__ import annotations

ATTR_DRIVE = "Drive"
ATTR_ENABLED = "Sensor Enabled"
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
ATTR_UPTIME = "Uptime"
ATTR_VOLUME_SIZE = "Volume Size"

PLATFORMS = ["sensor"]
DEFAULT_NAME = "QNAP"
DEFAULT_PORT = 8080
DEFAULT_TIMEOUT = 5
DOMAIN = "qnap"

NOTIFICATION_ID = "qnap_notification"
NOTIFICATION_TITLE = "QNAP Sensor Setup"
VOLUME_NAME = "volume"

BAS_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "basic"]
CPU_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "cpu"]
MEM_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "memory"]
NET_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "network"]
DRI_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "drive"]
FOL_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "folder"]
VOL_SENSOR = [desc for desc in SENSOR_TYPES if desc.stype == "volume"]
