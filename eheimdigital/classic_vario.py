"""The Eheim Digital classicVARIO filter."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from .device import EheimDigitalDevice
from .types import (
    ClassicVarioDataPacket,
    FilterErrorCode,
    FilterMode,
    MsgTitle,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalClassicVario(EheimDigitalDevice):
    """Represent a Eheim Digital classicVARIO filter."""

    classic_vario_data: ClassicVarioDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a classicVARIO filter."""
        super().__init__(hub, usrdta)

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.CLASSIC_VARIO_DATA:
            self.classic_vario_data = ClassicVarioDataPacket(**msg)

    @override
    async def update(self) -> None:
        """Get the new filter state."""
        await self.hub.send_packet({
            "title": MsgTitle.GET_CLASSIC_VARIO_DATA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def set_classic_vario_param(self, data: dict[str, Any]) -> None:
        """Send a SET_CLASSIC_VARIO_PARAM packet, containing new values from data."""
        if self.classic_vario_data is None:
            _LOGGER.error(
                "set_classic_vario_param: No CLASSIC_VARIO_DATA packet received yet."
            )
            return
        await self.hub.send_packet({
            "title": "SET_CLASSIC_VARIO_PARAM",
            "to": self.classic_vario_data["from"],
            "filterActive": self.classic_vario_data["filterActive"],
            "rel_manual_motor_speed": self.classic_vario_data["rel_manual_motor_speed"],
            "rel_motor_speed_day": self.classic_vario_data["rel_motor_speed_day"],
            "rel_motor_speed_night": self.classic_vario_data["rel_motor_speed_night"],
            "startTime_day": self.classic_vario_data["startTime_day"],
            "startTime_night": self.classic_vario_data["startTime_night"],
            "pulse_motorSpeed_High": self.classic_vario_data["pulse_motorSpeed_High"],
            "pulse_motorSpeed_Low": self.classic_vario_data["pulse_motorSpeed_Low"],
            "pulse_Time_High": self.classic_vario_data["pulse_Time_High"],
            "pulse_Time_Low": self.classic_vario_data["pulse_Time_Low"],
            "pumpMode": self.classic_vario_data["pumpMode"],
            "from": "USER",
            **data,
        })

    @property
    def is_active(self) -> bool | None:
        """Return whether the filter is active."""
        if self.classic_vario_data is None:
            return None
        return bool(self.classic_vario_data["filterActive"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the filter should be active or not."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"filterActive": int(active)})

    @property
    def current_speed(self) -> int | None:
        """Return the current filter pump speed."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["rel_speed"]

    @property
    def manual_speed(self) -> int | None:
        """Return the manual filter pump speed."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["rel_manual_motor_speed"]

    async def set_manual_speed(self, speed: int) -> None:
        """Set the filter speed in manual mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"rel_manual_motor_speed": speed})

    @property
    def day_speed(self) -> int | None:
        """Return the day filter pump speed in Bio mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["rel_motor_speed_day"]

    async def set_day_speed(self, speed: int) -> None:
        """Set the day filter speed in Bio mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"rel_motor_speed_day": speed})

    @property
    def night_speed(self) -> int | None:
        """Return the night filter pump speed in Bio mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["rel_motor_speed_night"]

    async def set_night_speed(self, speed: int) -> None:
        """Set the night filter speed in Bio mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"rel_motor_speed_night": speed})

    @property
    def day_start_time(self) -> time | None:
        """Return the day start time for Bio mode."""
        if self.classic_vario_data is None:
            return None
        return time(
            self.classic_vario_data["startTime_day"] // 60,
            self.classic_vario_data["startTime_day"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_day_start_time(self, day_start_time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.classic_vario_data is None:
            return
        t = (
            datetime(
                2020,
                1,
                1,
                day_start_time.hour,
                day_start_time.minute,
                tzinfo=day_start_time.tzinfo,
            )
            .astimezone(timezone(timedelta(minutes=self.usrdta["timezone"])))
            .time()
        )
        await self.set_classic_vario_param({"startTime_day": t.hour * 60 + t.minute})

    @property
    def night_start_time(self) -> time | None:
        """Return the night start time for Bio mode."""
        if self.classic_vario_data is None:
            return None
        return time(
            self.classic_vario_data["startTime_night"] // 60,
            self.classic_vario_data["startTime_night"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_night_start_time(self, night_start_time: time) -> None:
        """Set the night start time for Bio mode."""
        if self.classic_vario_data is None:
            return
        t = (
            datetime(
                2020,
                1,
                1,
                night_start_time.hour,
                night_start_time.minute,
                tzinfo=night_start_time.tzinfo,
            )
            .astimezone(timezone(timedelta(minutes=self.usrdta["timezone"])))
            .time()
        )
        await self.set_classic_vario_param({"startTime_night": t.hour * 60 + t.minute})

    @property
    def high_pulse_speed(self) -> int | None:
        """Return pulse speed for high pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["pulse_motorSpeed_High"]

    async def set_high_pulse_speed(self, pulse_high: int) -> None:
        """Set pulse speed for high pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"pulse_motorSpeed_High": pulse_high})

    @property
    def low_pulse_speed(self) -> int | None:
        """Return pulse speed for low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["pulse_motorSpeed_Low"]

    async def set_low_pulse_speed(self, pulse_low: int) -> None:
        """Set pulse speed for low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"pulse_motorSpeed_Low": pulse_low})

    @property
    def pulse_speeds(self) -> tuple[int, int] | None:
        """Return pulse speeds for high and low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return None
        return (
            self.classic_vario_data["pulse_motorSpeed_High"],
            self.classic_vario_data["pulse_motorSpeed_Low"],
        )

    async def set_pulse_speeds(self, pulse_high: int, pulse_low: int) -> None:
        """Set pulse speeds for high and low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({
            "pulse_motorSpeed_High": pulse_high,
            "pulse_motorSpeed_Low": pulse_low,
        })

    @property
    def high_pulse_time(self) -> int | None:
        """Return pulse time for high pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["pulse_Time_High"]

    async def set_high_pulse_time(self, pulse_high: int) -> None:
        """Set pulse time for high pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"pulse_Time_High": pulse_high})

    @property
    def low_pulse_time(self) -> int | None:
        """Return pulse time for low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["pulse_Time_Low"]

    async def set_low_pulse_time(self, pulse_low: int) -> None:
        """Set pulse time for low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"pulse_Time_Low": pulse_low})

    @property
    def pulse_times(self) -> tuple[int, int] | None:
        """Return pulse times for high and low pulse in Pulse mode in seconds."""
        if self.classic_vario_data is None:
            return None
        return (
            self.classic_vario_data["pulse_Time_High"],
            self.classic_vario_data["pulse_Time_Low"],
        )

    async def set_pulse_times(self, pulse_high: int, pulse_low: int) -> None:
        """Set pulse times in seconds for high and low pulse in Pulse mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({
            "pulse_Time_High": pulse_high,
            "pulse_Time_Low": pulse_low,
        })

    @property
    def service_hours(self) -> int | None:
        """Return the amount of hours until the next service is needed."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["serviceHour"]

    @property
    def filter_mode(self) -> FilterMode | None:
        """Return the current filter mode."""
        if self.classic_vario_data is None:
            return None
        return FilterMode(self.classic_vario_data["pumpMode"])

    async def set_filter_mode(self, value: FilterMode) -> None:
        """Set the filter mode."""
        if self.classic_vario_data is None:
            return
        await self.set_classic_vario_param({"pumpMode": value.value})

    @property
    def turn_off_time(self) -> int | None:
        """Return the remaining turn off time in seconds."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["turnOffTime"]

    @property
    def turn_feeding_time(self) -> int | None:
        """Return the remaining pause time after the autofeeder sent a pause signal."""
        if self.classic_vario_data is None:
            return None
        return self.classic_vario_data["turnTimeFeeding"]

    @property
    def error_code(self) -> FilterErrorCode | None:
        """Return the current error code of the filter."""
        if self.classic_vario_data is None:
            return None
        return FilterErrorCode(self.classic_vario_data["errorCode"])

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "classic_vario_data": self.classic_vario_data,
            **super().as_dict(),
        }
