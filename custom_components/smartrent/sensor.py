"""Platform for sensor integration."""

from typing import Optional, Union

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.helpers.device_registry import DeviceEntryType
from smartrent import DoorLock, Sensor, Thermostat
from smartrent.api import API

from .const import CONFIGURATION_URL, PROPER_NAME


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    client: API = hass.data["smartrent"][entry.entry_id]

    for thermo in client.get_thermostats():
        async_add_entities(
            [
                SmartrentSensor(thermo, "current_temp", "temperature"),
                SmartrentSensor(thermo, "mode"),
            ]
        )
        if thermo.get_fan_mode():
            async_add_entities([SmartrentSensor(thermo, "fan_mode")])
        if thermo.get_current_humidity():
            async_add_entities(
                [SmartrentSensor(thermo, "current_humidity", "humidity")]
            )

    for lock in client.get_locks():
        async_add_entities(
            [
                SmartrentSensor(lock, "battery_level", "battery"),
                SmartrentSensor(lock, "notification"),
                SmartrentSensor(lock, "locked"),
                SmartrentCommandLatencySensor(lock),
            ]
        )

    for leak_sensor in client.get_leak_sensors():
        async_add_entities([SmartrentSensor(leak_sensor, "battery_level", "battery")])

    for motion_sensor in client.get_motion_sensors():
        async_add_entities([SmartrentSensor(motion_sensor, "battery_level", "battery")])


class SmartrentSensor(SensorEntity):
    def __init__(
        self,
        device: Union[DoorLock, Thermostat, Sensor],
        sensor_name: str,
        device_class: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.device = device
        self.sensor_name = sensor_name
        self._device_class = device_class

        self.device.start_updater()
        self.device.set_update_callback(self.async_schedule_update_ha_state)

    @property
    def available(self) -> bool:
        """Cloud connection is up and the device reports online."""
        return self.device.get_reachable() and self.device.get_online() is not False

    @property
    def should_poll(self):
        """Return the polling state, if needed."""
        return False

    @property
    def unique_id(self):
        sname_id = "".join([str(ord(char)) for char in self.sensor_name])
        uid = str(self.device._device_id) + str(sname_id)

        return uid

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self.device._name + " " + self.sensor_name

    @property
    def native_value(self):
        """Return native value for entity."""
        return getattr(self.device, f"get_{self.sensor_name}")()

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT if self._device_class else None

    @property
    def native_unit_of_measurement(self):
        if self._device_class == "temperature":
            return UnitOfTemperature.FAHRENHEIT
        if self._device_class in ["humidity", "battery"]:
            return PERCENTAGE

    @property
    def device_info(self):
        return dict(
            identifiers={("id", self.device._device_id)},
            manufacturer=PROPER_NAME,
            model=str(self.device.__class__.__name__),
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=CONFIGURATION_URL,
        )


class SmartrentCommandLatencySensor(SensorEntity):
    """
    Seconds from sending the last lock/unlock to the hub reporting it done.

    Diagnostic: graph it to see the hub's health, alert on the ``outcome``
    attribute turning ``failed``. Unknown until the first command; stays at
    the last confirmed latency after an ``unchanged`` no-op.
    """

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False
    _attr_icon = "mdi:timer-outline"

    def __init__(self, device: DoorLock) -> None:
        super().__init__()
        self.device = device
        self.device.start_updater()
        self.device.set_update_callback(self.async_schedule_update_ha_state)

    @property
    def available(self) -> bool:
        return self.device.get_reachable()

    @property
    def unique_id(self):
        return f"{self.device._device_id}_command_latency"

    @property
    def name(self):
        return f"{self.device._name} command latency"

    @property
    def native_value(self):
        result = self.device.get_last_command()
        if result is None or result.outcome == "pending":
            return None if result is None else self._attr_native_value
        if result.outcome == "confirmed":
            self._attr_native_value = result.latency
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        result = self.device.get_last_command()
        if result is None:
            return {}
        return {
            "outcome": result.outcome,
            "attempts": result.attempts,
            "attribute": result.attribute,
            "value": result.value,
            "started": result.started.isoformat(),
            "verified": result.verified,
            "error": result.error,
        }

    @property
    def device_info(self):
        return dict(
            identifiers={("id", self.device._device_id)},
            manufacturer=PROPER_NAME,
            model=str(self.device.__class__.__name__),
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=CONFIGURATION_URL,
        )
