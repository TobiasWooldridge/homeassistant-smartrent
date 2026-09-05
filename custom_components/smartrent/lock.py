"""Platform for lock integration."""
import logging
from typing import Any, Union

from homeassistant.components.lock import LockEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType
from smartrent import DoorLock
from smartrent.utils import CommandFailedError

from .const import CONFIGURATION_URL, PROPER_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup lock platform."""
    client = hass.data["smartrent"][entry.entry_id]
    locks = client.get_locks()
    for lock in locks:
        async_add_entities([SmartrentLock(lock)])


class SmartrentLock(LockEntity):
    def __init__(self, lock: DoorLock) -> None:
        super().__init__()
        self.device = lock

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
        """Return a unique ID."""
        return str(self.device._device_id)

    @property
    def name(self):
        """Return the display name of this lock."""
        return self.device._name

    @property
    def changed_by(self) -> Union[str, None]:
        return self.device.get_notification()

    @property
    def is_locked(self) -> Union[bool, None]:
        return self.device.get_locked()

    @property
    def is_jammed(self) -> Union[bool, None]:
        return "ALARM_TYPE_9" in str(self.device.get_notification())

    @property
    def is_locking(self) -> bool:
        """A lock command is awaiting the hub's report."""
        return self.device.get_pending_locked() is True

    @property
    def is_unlocking(self) -> bool:
        """An unlock command is awaiting the hub's report."""
        return self.device.get_pending_locked() is False

    async def async_lock(self, **kwargs: Any):
        await self._async_set_locked(True)

    async def async_unlock(self, **kwargs: Any):
        await self._async_set_locked(False)

    async def _async_set_locked(self, value: bool):
        """
        Returns once the hub has reported the new state. The library re-sends
        once and raises if the hub never reports; that becomes a service-call
        error here so automations and the UI see the failure instead of a lock
        that silently stayed put.
        """
        try:
            await self.device.async_set_locked(value)
        except CommandFailedError as err:
            raise HomeAssistantError(str(err)) from err

    @property
    def device_info(self):
        return dict(
            identifiers={("id", self.device._device_id)},
            name=str(self.name),
            manufacturer=PROPER_NAME,
            model=str(self.device.__class__.__name__),
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=CONFIGURATION_URL,
        )
