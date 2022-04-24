"""Class to represent dali lamps."""
import json
import logging

import dali.gear.general as gear
from consts import (ALL_SUPPORTED_LOG_LEVELS, LOG_FORMAT, MQTT_AVAILABLE,
                    MQTT_BRIGHTNESS_COMMAND_TOPIC, MQTT_BRIGHTNESS_STATE_TOPIC,
                    MQTT_COMMAND_TOPIC, MQTT_DALI2MQTT_STATUS,
                    MQTT_NOT_AVAILABLE, MQTT_PAYLOAD_OFF, MQTT_STATE_TOPIC,
                    __author__, __email__, __version__)
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
        min_physical_level,
        min_level,
        level,
        max_level,
    ):
        """Initialize Lamp."""
        self.driver = driver
        self.short_address = short_address
        self.friendly_name = friendly_name
        self.device_name = slugify(friendly_name)
        self.min_physical_level = min_physical_level
        self.min_level = min_level
        self.max_level = max_level
        self.level = level
        logger.setLevel(ALL_SUPPORTED_LOG_LEVELS[log_level])

    def gen_ha_config(self, mqtt_base_topic):
        """Generate a automatic configuration for Home Assistant."""
        json_config = {
            "name": self.friendly_name,
            "obj_id": f"dali_light_{self.device_name}",
            "uniq_id": f"{type(self.driver).__name__}_{self.short_address}",
            "stat_t": MQTT_STATE_TOPIC.format(mqtt_base_topic, self.device_name),
            "cmd_t": MQTT_COMMAND_TOPIC.format(
                mqtt_base_topic, self.device_name
            ),
            "pl_off": MQTT_PAYLOAD_OFF.decode('utf-8'),
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

    @property
    def level(self):
        """Return brightness level."""
        return self.__level

    @level.setter
    def level(self, value):
        if not self.min_level <= value <= self.max_level and value != 0:
            raise ValueError
        self.__level = value
        self.driver.send(gear.DAPC(self.short_address, self.level))
        logger.debug(
            "Set lamp <%s> brightness level to %s", self.friendly_name, self.level
        )
