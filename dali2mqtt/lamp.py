"""Class to represent dali lamps."""
import json
import logging

import dali.gear.general as gear
import dali.address as address
from dali2mqtt.consts import (
    ALL_SUPPORTED_LOG_LEVELS,
    LOG_FORMAT,
    MQTT_AVAILABLE,
    MQTT_BRIGHTNESS_COMMAND_TOPIC,
    MQTT_BRIGHTNESS_STATE_TOPIC,
    MQTT_COMMAND_TOPIC,
    MQTT_DALI2MQTT_STATUS,
    MQTT_NOT_AVAILABLE,
    MQTT_PAYLOAD_OFF,
    MQTT_STATE_TOPIC,
    __version__,
)
from slugify import slugify

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class Lamp:
    """Representation of a DALI Lamp."""

    def __init__(
        self,
        log_level,
        driver,
        friendly_name,
        short_address,
    ):
        """Initialize Lamp."""
        self.driver = driver
        self.short_address = short_address
        self.friendly_name = friendly_name
        self.associated_lamps = None

        self.device_name = slugify(friendly_name)

        logger.setLevel(ALL_SUPPORTED_LOG_LEVELS[log_level])

        _min_physical_level = driver.send(gear.QueryPhysicalMinimum(short_address))

        try:
            self.min_physical_level = _min_physical_level.value
        except Exception as err:
            self.min_physical_level = None
            logger.warning("Set min_physical_level to None as %s failed: %s", _min_physical_level, err)
        self.min_level = driver.send(gear.QueryMinLevel(short_address)).value
        if not isinstance(self.min_level, int):
            self.min_level = self.min_physical_level if self.min_physical_level else 86
        self.max_level = driver.send(gear.QueryMaxLevel(short_address)).value
        if not isinstance(self.max_level, int):
            self.max_level = 254
        self.level = driver.send(gear.QueryActualLevel(short_address)).value

    def gen_ha_config(self, mqtt_base_topic):
        """Generate a automatic configuration for Home Assistant."""
        json_config = {
            "name": self.friendly_name,
            "obj_id": f"dali_light_{self.device_name}",
            "uniq_id": f"{type(self.driver).__name__}_{self.short_address}",
            "stat_t": MQTT_STATE_TOPIC.format(mqtt_base_topic, self.device_name),
            "cmd_t": MQTT_COMMAND_TOPIC.format(mqtt_base_topic, self.device_name),
            "pl_off": MQTT_PAYLOAD_OFF.decode("utf-8"),
            "bri_stat_t": MQTT_BRIGHTNESS_STATE_TOPIC.format(
                mqtt_base_topic, self.device_name
            ),
            "bri_cmd_t": MQTT_BRIGHTNESS_COMMAND_TOPIC.format(
                mqtt_base_topic, self.device_name
            ),
            "bri_scl": self.max_level,
            "on_cmd_type": "brightness",
            "avty_t": MQTT_DALI2MQTT_STATUS.format(mqtt_base_topic),
            "pl_avail": MQTT_AVAILABLE,
            "pl_not_avail": MQTT_NOT_AVAILABLE,
            "device": {
                "ids": "dali2mqtt",
                "name": "DALI Lights",
                "sw": f"dali2mqtt {__version__}",
                "mdl": f"{type(self.driver).__name__}",
                "mf": "dali2mqtt",
            },
        }
        return json.dumps(json_config)

    def actual_level(self):
        """Retrieve actual level from ballast."""
        local_level = self.driver.send(gear.QueryActualLevel(self.short_address)).value
        if isinstance(local_level,int):
            self.__level = local_level
        else:
            self.__level = 0

    @property
    def level(self):
        """Return brightness level."""
        return self.__level

    @level.setter
    def level(self, value):
        """Commit level to ballast."""
        if isinstance(value, int) and value != 0:
            if isinstance(self.min_level, int) and value < self.min_level:
                value = self.min_level
            elif isinstance(self.max_level, int) and value > self.max_level:
                value = self.max_level

        if isinstance(value, int):
            self.__level = value
            self.driver.send(gear.DAPC(self.short_address, self.level))
            logger.debug(
                "Set lamp <%s> brightness level to %s", self.friendly_name, self.level
            )
        else:
            self.__level = 0
            
    def level_change_needed(self, value):
        if isinstance(value, int):
            if value == 0:
                return True
            
            if isinstance(self.min_level, int) and value < self.min_level:
                value = self.min_level
            elif isinstance(self.max_level, int) and value > self.max_level:
                value = self.max_level
                
            current_level = self.level
            return value != current_level
        return False
            


        
    def off(self):
        """Turn off ballast."""
        self.driver.send(gear.Off(self.short_address))
        self.__level = 0

    def __str__(self):
        """Serialize lamp information."""
        addr = self.short_address.address if hasattr(self.short_address,"address") else self.short_address
        return (
            f"{self.device_name} - address: {addr}, "
            f"actual brightness level: {self.level} (minimum: {self.min_level}, "
            f"max: {self.max_level}, physical minimum: {self.min_physical_level})"
        )
        
    def is_group(self):
        return isinstance(self.short_address, address.Group)
    
    def add_associated_lamp(self, assoc_lamp_object):
        if self.associated_lamps is None:
            self.associated_lamps = [] 
        self.associated_lamps.append(assoc_lamp_object)
