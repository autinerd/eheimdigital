"""The Eheim Digital professionel5e filter."""

from __future__ import annotations

from datetime import time, timedelta, timezone
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from .device import EheimDigitalDevice
from .types import (
    FilterDataPacket,
    FilterModeProf,
    MsgTitle,
    UnitOfMeasurement,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalFilter(EheimDigitalDevice):
    """Represent a Eheim Digital professionel 5e filter."""

    filter_data: FilterDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a professionel 5e filter."""
        super().__init__(hub, usrdta)

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.FILTER_DATA:
            self.filter_data = FilterDataPacket(**msg)

    @override
    async def update(self) -> None:
        await self.hub.send_packet({
            "title": MsgTitle.GET_FILTER_DATA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def start_filter_normal_mode_without_comp(self, data: dict[str, Any]) -> None:
        """Start the filter in manual mode."""
        if self.filter_data is None:
            _LOGGER.error(
                "start_filter_normal_mode_without_comp: No filter data packet received yet!"
            )
            return
        await self.hub.send_packet({
            "title": "START_FILTER_NORMAL_MODE_WITHOUT_COMP",
            "to": self.filter_data["from"],
            "frequency": self.filter_data["freqSoll"],
            "from": "USER",
            **data,
        })

    async def start_filter_normal_mode_with_comp(self, data: dict[str, Any]) -> None:
        """Start the filter in constant flow mode."""
        if self.filter_data is None:
            _LOGGER.error(
                "start_filter_normal_mode_with_comp: No filter data packet received yet!"
            )
            return
        await self.hub.send_packet({
            "title": "START_FILTER_NORMAL_MODE_WITH_COMP",
            "to": self.filter_data["from"],
            "flow_rate": self.filter_data["sollStep"],
            "from": "USER",
            **data,
        })

    async def start_filter_pulse_mode(self, data: dict[str, Any]) -> None:
        """Start the filter in pulse mode."""
        if self.filter_data is None:
            _LOGGER.error(
                "start_filter_pulse_mode: No filter data packet received yet!"
            )
            return
        await self.hub.send_packet({
            "title": "START_FILTER_PULSE_MODE",
            "to": self.filter_data["from"],
            "time_high": self.filter_data["pm_time_high"],
            "time_low": self.filter_data["pm_time_low"],
            "dfs_soll_high": self.filter_data["pm_dfs_soll_high"],
            "dfs_soll_low": self.filter_data["pm_dfs_soll_low"],
            "from": "USER",
            **data,
        })

    async def start_nocturnal_mode(self, data: dict[str, Any]) -> None:
        """Start the filter in Bio mode."""
        if self.filter_data is None:
            _LOGGER.error("start_nocturnal_mode: No filter data packet received yet!")
            return
        await self.hub.send_packet({
            "title": "START_NOCTURNAL_MODE",
            "to": self.filter_data["from"],
            "dfs_soll_day": self.filter_data["nm_dfs_soll_day"],
            "dfs_soll_night": self.filter_data["nm_dfs_soll_night"],
            "end_time_night_mode": self.filter_data["end_time_night_mode"],
            "start_time_night_mode": self.filter_data["start_time_night_mode"],
            "sync": self.filter_data["sync"],
            "partnerName": self.filter_data["partnerName"],
            "from": "USER",
            **data,
        })

    async def set_filter_pump(self, data: dict[str, Any]) -> None:
        """Set the filter pump."""
        if self.filter_data is None:
            _LOGGER.error("set_filter_pump: No filter data packet received yet!")
            return
        await self.hub.send_packet({
            "title": MsgTitle.SET_FILTER_PUMP,
            "to": self.filter_data["from"],
            "active": self.filter_data["filterActive"],
            "from": "USER",
            **data,
        })

    @property
    def is_active(self) -> bool | None:
        """Return whether the filter is active."""
        if self.filter_data is None:
            return None
        return bool(self.filter_data["filterActive"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the filter should be active or not."""
        if self.filter_data is not None:
            return
        await self.set_filter_pump({"active": int(active)})

    @property
    def filter_mode(self) -> FilterModeProf | None:
        """Return the current filter mode."""
        if self.filter_data is None:
            return None
        return FilterModeProf(self.filter_data["pumpMode"] & 255)

    async def set_filter_mode(self, mode: FilterModeProf) -> None:
        """Set the filter mode."""
        match mode:
            case FilterModeProf.MANUAL:
                await self.start_filter_normal_mode_without_comp({})
            case FilterModeProf.CONSTANT_FLOW:
                await self.start_filter_normal_mode_with_comp({})
            case FilterModeProf.PULSE:
                await self.start_filter_pulse_mode({})
            case FilterModeProf.BIO:
                await self.start_nocturnal_mode({})

    @property
    def current_speed(self) -> float | None:
        """Return the current filter pump speed."""
        if self.filter_data is None:
            return None
        return (float)(self.filter_data["freq"]) / 100.0

    @property
    def manual_speed(self) -> float | None:
        """Return the manual filter pump speed."""
        if self.filter_data is None:
            return None
        return self.filter_data["freqSoll"] / 100

    async def set_manual_speed(self, speed: float) -> None:
        """Set the filter speed in manual mode."""
        if self.filter_data is not None:
            await self.start_filter_normal_mode_without_comp({
                "frequency": int(speed * 100),
            })

    @property
    def const_flow(self) -> int | None:
        """Return the constant flow index in constant flow mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["sollStep"]

    async def set_const_flow(self, flow_ind: int) -> None:
        """Set the flow index in constant flow mode."""
        if self.filter_data is None:
            return
        await self.start_filter_normal_mode_with_comp({
            "flow_rate": flow_ind,
        })

    @property
    def day_speed(self) -> int | None:
        """Return the day filter pump speed in Bio mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["nm_dfs_soll_day"]

    async def set_day_speed(self, speed: int) -> None:
        """Set the day filter speed in Bio mode."""
        if self.filter_data is not None:
            self.filter_data["nm_dfs_soll_day"] = speed
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def night_speed(self) -> int | None:
        """Return the night filter pump speed in Bio mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["nm_dfs_soll_night"]

    async def set_night_speed(self, speed: int) -> None:
        """Set the night filter speed in Bio mode."""
        if self.filter_data is not None:
            self.filter_data["nm_dfs_soll_night"] = speed
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def day_start_time(self) -> time | None:
        """Return the day start time for Bio mode."""
        if self.filter_data is None:
            return None
        return time(
            self.filter_data["end_time_night_mode"] // 60,
            self.filter_data["end_time_night_mode"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_day_start_time(self, time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.filter_data is not None:
            self.filter_data["end_time_night_mode"] = time.hour * 60 + time.minute
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def night_start_time(self) -> time | None:
        """Return the night start time for Bio mode."""
        if self.filter_data is None:
            return None
        return time(
            self.filter_data["start_time_night_mode"] // 60,
            self.filter_data["start_time_night_mode"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_night_start_time(self, time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.filter_data is not None:
            self.filter_data["start_time_night_mode"] = time.hour * 60 + time.minute
            await self.set_filter_mode(FilterModeProf.BIO)

    @property
    def high_pulse_speed(self) -> int | None:
        """Return pulse speed for high in Pulse mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["pm_dfs_soll_high"]

    async def set_high_pulse_speed(self, speed: int) -> None:
        """Set pulse speed for high in Pulse mode."""
        if self.filter_data is not None:
            self.filter_data["pm_dfs_soll_high"] = speed
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def low_pulse_speed(self) -> int | None:
        """Return pulse speed for low pulse in Pulse mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["pm_dfs_soll_low"]

    async def set_low_pulse_speed(self, speed: int) -> None:
        """Set pulse speed for low in Pulse mode."""
        if self.filter_data is not None:
            self.filter_data["pm_dfs_soll_low"] = speed
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def pulse_speeds(self) -> tuple[int, int] | None:
        """Return pulse speeds for high and low pulse in Pulse mode."""
        if self.filter_data is None:
            return None
        return (
            self.filter_data["pm_dfs_soll_high"],
            self.filter_data["pm_dfs_soll_low"],
        )

    @property
    def high_pulse_time(self) -> int | None:
        """Return pulse time for high pulse in Pulse mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["pm_time_high"]

    async def set_high_pulse_time(self, time: int) -> None:
        """Set pulse time for high in Pulse mode."""
        if self.filter_data is not None:
            self.filter_data["pm_time_high"] = time
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def low_pulse_time(self) -> int | None:
        """Return pulse time for low pulse in Pulse mode."""
        if self.filter_data is None:
            return None
        return self.filter_data["pm_time_low"]

    async def set_low_pulse_time(self, time: int) -> None:
        """Set pulse time for low in Pulse mode."""
        if self.filter_data is not None:
            self.filter_data["pm_time_low"] = time
            await self.set_filter_mode(FilterModeProf.PULSE)

    @property
    def pulse_times(self) -> tuple[int, int] | None:
        """Return pulse times for high and low pulse in Pulse mode in seconds."""
        if self.filter_data is None:
            return None
        return (
            self.filter_data["pm_time_high"],
            self.filter_data["pm_time_low"],
        )

    @property
    def service_hours(self) -> int | None:
        """Return the amount of hours until the next service is needed."""
        if self.filter_data is None:
            return None
        return self.filter_data["serviceHour"]

    @property
    def operating_time(self) -> int | None:
        """Return operating time in minutes."""
        if self.filter_data is None:
            return None
        return self.filter_data["runTime"]

    @property
    def turn_off_time(self) -> int | None:
        """Return the remaining turn off time in seconds."""
        if self.filter_data is None:
            return None
        return self.filter_data["turnOffTime"]

    @property
    def turn_feeding_time(self) -> int | None:
        """Return the remaining pause time after the autofeeder sent a pause signal."""
        if self.filter_data is None:
            return None
        return self.filter_data["turnTimeFeeding"]

    @cached_property
    def filter_model_name(self) -> str | None:
        """Return the filter model name."""
        if self.filter_data is None:
            return None
        match self.filter_data["version"]:
            case 74:
                return "professionel 5e 350"
            case 76:
                return "professionel 5e 450"
            case 78:
                return (
                    "professionel 5e 600T"
                    if self.usrdta["tankconfig"] == "WITH_THERMO"
                    else "professionel 5e 700"
                )
            case _:
                return "professionel 5e"

    @cached_property
    def filter_manual_values(self) -> list[float] | None:
        """Return the allowed manual values for the filter depending on the model.

        The values are in Hz and represent the rotation speed of the pump.
        """
        if self.filter_data is None:
            return None
        match self.filter_data["version"]:
            case 74:
                return [
                    35,
                    37.5,
                    40.5,
                    43,
                    45.5,
                    48,
                    51,
                    53.5,
                    56,
                    59,
                    61.5,
                    64,
                    66.5,
                    69.5,
                    72,
                ]
            case 76:
                return [
                    35,
                    38,
                    41,
                    44,
                    46.5,
                    49.5,
                    52.5,
                    55.5,
                    58.5,
                    61.5,
                    64.5,
                    67,
                    70,
                    73,
                    76,
                ]
            case 78:
                return [
                    35,
                    38,
                    41.5,
                    44.5,
                    48,
                    51,
                    54,
                    57.5,
                    60.5,
                    64,
                    67,
                    70,
                    73.5,
                    76.5,
                    80,
                ]
            case _:
                return None

    @cached_property
    def filter_const_flow_values(self) -> list[int] | None:
        """Return the flow rate values for constant flow mode.

        The values are in liters or gallons per hour, depending on the unit setting.
        """
        if self.filter_data is None:
            return None
        match self.filter_data["version"]:
            case 74:
                return (
                    [
                        400,
                        440,
                        480,
                        515,
                        550,
                        585,
                        620,
                        650,
                        680,
                        710,
                        740,
                        770,
                        800,
                        830,
                        860,
                    ]
                    if self.usrdta["unit"] == int(UnitOfMeasurement.METRIC)
                    else [
                        110,
                        120,
                        130,
                        140,
                        145,
                        155,
                        165,
                        175,
                        180,
                        190,
                        195,
                        205,
                        215,
                        220,
                        230,
                    ]
                )
            case 76:
                return (
                    [
                        400,
                        460,
                        515,
                        565,
                        610,
                        650,
                        690,
                        730,
                        770,
                        805,
                        840,
                        875,
                        910,
                        945,
                        980,
                    ]
                    if self.usrdta["unit"] == int(UnitOfMeasurement.METRIC)
                    else [
                        110,
                        125,
                        140,
                        150,
                        165,
                        175,
                        185,
                        195,
                        205,
                        215,
                        225,
                        235,
                        240,
                        250,
                        260,
                    ]
                )
            case 78:
                return (
                    [
                        400,
                        470,
                        540,
                        600,
                        650,
                        700,
                        745,
                        785,
                        825,
                        865,
                        905,
                        945,
                        985,
                        1025,
                        1065,
                    ]
                    if self.usrdta["unit"] == int(UnitOfMeasurement.METRIC)
                    else [
                        110,
                        125,
                        145,
                        165,
                        175,
                        185,
                        200,
                        210,
                        220,
                        230,
                        240,
                        250,
                        260,
                        275,
                        285,
                    ]
                )
            case _:
                return None

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "filter_data": self.filter_data,
            **super().as_dict(),
        }
