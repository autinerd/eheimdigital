"""The Eheim Digital professionel5e filter."""

from __future__ import annotations

from datetime import time, timedelta, timezone
from logging import getLogger
from typing import TYPE_CHECKING, Any, override
from functools import cached_property

from .device import EheimDigitalDevice
from .types import professionel5eDataPacket, FilterModeProf, MsgTitle, UsrDtaPacket

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalProfessionel5e(EheimDigitalDevice):
    """Represent a Eheim Digital Professionel5e filter."""

    data_paket: professionel5eDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a Professionel5e filter."""
        super().__init__(hub, usrdta)

    @cached_property
    def sw_version(self) -> str:
        """Device software version with formating and order like on Eheim page."""
        rv0, rv1 = self.usrdta["revision"]
        return f"{rv1 // 1000}.{(rv1 % 1000) // 10:02}.{rv1 % 10} (page) {rv0 // 1000}.{(rv0 % 1000) // 10:02}.{rv0 % 10} (server)"

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.PROF_5E_DATA:
            self.data_paket = professionel5eDataPacket(**msg)

    @override
    async def update(self) -> None:
        """Get the new filter state."""
        msg = {
            "title": MsgTitle.PROF_5E_GET_DATA.value,
            "to": self.mac_address,
            "from": "USER",
        }
        _LOGGER.info(f"Filter data request to professionel5e: {msg}")
        await self.hub.send_packet(msg)

    async def filter_command(self, title: MsgTitle, data: dict[str, Any]) -> None:
        """Send a filter command with parameter."""
        if self.data_paket is None:
            _LOGGER.error(f"No filter data packet received yet! Can not send {title}, {data}")
            return
        msg = {
            "title": title.value,
            "to": self.data_paket["from"],
            "from": "USER_OPT",
            **data,
        }
        _LOGGER.info(f"Command to professionel5e: {msg}")
        await self.hub.send_packet(msg)

    @property
    def is_active(self) -> bool | None:
        """Return whether the filter is active."""
        if self.data_paket is None:
            return None
        return bool(self.data_paket["filterActive"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the filter should be active or not."""
        if self.data_paket is not None:
            self.data_paket["filterActive"] = int(active)
        await self.filter_command(MsgTitle.PROF_5E_PUMP, {"active": int(active)})

    @property
    def filter_mode(self) -> FilterModeProf | None:
        """Return the current filter mode."""
        try:
            return FilterModeProf(self.data_paket["pumpMode"]) if self.data_paket is not None else None
        except ValueError:
            _LOGGER.error(f"Invalid Punp Mode (calibration): {self.data_paket['pumpMode']}")
            return None

    async def set_filter_mode(self, mode: FilterModeProf) -> None:
        """Set the filter mode."""
        match mode:
            case FilterModeProf.MANUAL:
                await self.filter_command(MsgTitle.PROF_5E_MANUAL, {"frequency": self.data_paket["freq"]})
            case FilterModeProf.CONSTANT:
                await self.filter_command(MsgTitle.PROF_5E_CONSTANT, {"flow_rate": self.data_paket["sollStep"]})
            case FilterModeProf.PULSE:
                await self.filter_command(
                    MsgTitle.PROF_5E_PULSE,
                    {
                        "time_high": self.data_paket["pm_time_high"],
                        "time_low": self.data_paket["pm_time_low"],
                        "dfs_soll_high": self.data_paket["pm_dfs_soll_high"],
                        "dfs_soll_low": self.data_paket["pm_dfs_soll_low"],
                    },
                )
            case FilterModeProf.BIO:
                await self.filter_command(
                    MsgTitle.PROF_5E_BIO,
                    {
                        "dfs_soll_day": self.data_paket["nm_dfs_soll_day"],
                        "dfs_soll_night": self.data_paket["nm_dfs_soll_night"],
                        "end_time_night_mode": self.data_paket["end_time_night_mode"],
                        "start_time_night_mode": self.data_paket["start_time_night_mode"],
                        "sync": self.data_paket["sync"],
                        "partnerName": self.data_paket["partnerName"],
                    },
                )

    @property
    def current_speed(self) -> float | None:
        """Return the current filter pump speed."""
        return (float)(self.data_paket["freq"]) / 100.0 if self.data_paket is not None else None

    @property
    def manual_speed(self) -> int | None:
        """Return the manual filter pump speed."""
        return self.data_paket["freqSoll"] / 100 if self.data_paket is not None else None

    async def set_manual_speed(self, speed: int) -> None:
        """Set the filter speed in manual mode."""
        if self.data_paket is not None:
            self.data_paket["freq"] = speed * 100
            await self.set_filter_mode(FilterModeProf.MANUAL)

    @property
    def const_flow(self) -> int | None:
        """Return the constant flow index in constant flow mode."""
        return self.data_paket["sollStep"] if self.data_paket is not None else None

    async def set_const_flow(self, flow_ind: int) -> None:
        """Set the flow index in constant flow mode."""
        if self.data_paket is not None:
            self.data_paket["sollStep"] = flow_ind
            await self.set_filter_mode(FilterModeProf.CONSTANT)

    @property
    def day_speed(self) -> int | None:
        """Return the day filter pump speed in Bio mode."""
        return self.data_paket["nm_dfs_soll_day"] if self.data_paket is not None else None

    async def set_day_speed(self, speed: int) -> None:
        """Set the day filter speed in Bio mode."""
        if self.data_paket is not None:
            self.data_paket["nm_dfs_soll_day"] = speed
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def night_speed(self) -> int | None:
        """Return the night filter pump speed in Bio mode."""
        return self.data_paket["nm_dfs_soll_night"] if self.data_paket is not None else None

    async def set_night_speed(self, speed: int) -> None:
        """Set the night filter speed in Bio mode."""
        if self.data_paket is not None:
            self.data_paket["nm_dfs_soll_night"] = speed
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def day_start_time(self) -> time | None:
        """Return the day start time for Bio mode."""
        return (
            time(
                self.data_paket["end_time_night_mode"] // 60,
                self.data_paket["end_time_night_mode"] % 60,
                tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
            )
            if self.data_paket is not None
            else None
        )

    async def set_day_start_time(self, time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.data_paket is not None:
            self.data_paket["end_time_night_mode"] = time.hour * 60 + time.minute
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def night_start_time(self) -> time | None:
        """Return the night start time for Bio mode."""
        return (
            time(
                self.data_paket["start_time_night_mode"] // 60,
                self.data_paket["start_time_night_mode"] % 60,
                tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
            )
            if self.data_paket is not None
            else None
        )

    async def set_night_start_time(self, time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.data_paket is not None:
            self.data_paket["start_time_night_mode"] = time.hour * 60 + time.minute
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def high_pulse_speed(self) -> int | None:
        """Return pulse speed for high in Pulse mode."""
        return self.data_paket["pm_dfs_soll_high"] if self.data_paket is not None else None

    async def set_high_pulse_speed(self, speed: int) -> None:
        """Set pulse speed for high in Pulse mode."""
        if self.data_paket is not None:
            self.data_paket["pm_dfs_soll_high"] = speed
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def low_pulse_speed(self) -> int | None:
        """Return pulse speed for low pulse in Pulse mode."""
        return self.data_paket["pm_dfs_soll_low"] if self.data_paket is not None else None

    async def set_low_pulse_speed(self, speed: int) -> None:
        """Set pulse speed for low in Pulse mode."""
        if self.data_paket is not None:
            self.data_paket["pm_dfs_soll_low"] = speed
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def pulse_speeds(self) -> tuple[int, int] | None:
        """Return pulse speeds for high and low pulse in Pulse mode."""
        return (
            (
                self.data_paket["pm_dfs_soll_high"],
                self.data_paket["pm_dfs_soll_low"],
            )
            if self.data_paket is not None
            else None
        )

    @property
    def high_pulse_time(self) -> int | None:
        """Return pulse time for high pulse in Pulse mode."""
        return self.data_paket["pm_time_high"] if self.data_paket is not None else None

    async def set_high_pulse_time(self, time: int) -> None:
        """Set pulse time for high in Pulse mode."""
        if self.data_paket is not None:
            self.data_paket["pm_time_high"] = time
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def low_pulse_time(self) -> int | None:
        """Return pulse time for low pulse in Pulse mode."""
        return self.data_paket["pm_time_low"] if self.data_paket is not None else None

    async def set_low_pulse_time(self, time: int) -> None:
        """Set pulse time for low in Pulse mode."""
        if self.data_paket is not None:
            self.data_paket["pm_time_low"] = time
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def pulse_times(self) -> tuple[int, int] | None:
        """Return pulse times for high and low pulse in Pulse mode in seconds."""
        return (
            (
                self.data_paket["pm_time_high"],
                self.data_paket["pm_time_low"],
            )
            if self.data_paket is not None
            else None
        )

    @property
    def service_hours(self) -> int | None:
        """Return the amount of hours until the next service is needed."""
        return self.data_paket["serviceHour"] if self.data_paket is not None else None

    @property
    def operating_time(self) -> int | None:
        """Return operating time [min]."""
        return self.data_paket["runTime"] if self.data_paket is not None else None

    @property
    def turn_off_time(self) -> int | None:
        """Return the remaining turn off time in seconds."""
        return self.data_paket["turnOffTime"] if self.data_paket is not None else None

    @property
    def turn_feeding_time(self) -> int | None:
        """Return the remaining pause time after the autofeeder sent a pause signal."""
        return self.data_paket["turnTimeFeeding"] if self.data_paket is not None else None

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "professionel5e_data": self.data_paket,
            **super().as_dict(),
        }
