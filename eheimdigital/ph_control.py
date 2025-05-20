"""The Eheim Digital pHcontrol device."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from .device import EheimDigitalDevice
from .types import (
    MsgTitle,
    PHControlErrorCode,
    PHControlMode,
    PHDataPacket,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from .hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalPHControl(EheimDigitalDevice):
    """Represent a EHEIM Digital pHcontrol device."""

    ph_data: PHDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a pHcontrol device."""
        super().__init__(hub, usrdta)

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.PH_DATA:
            self.ph_data = PHDataPacket(**msg)

    @override
    async def update(self) -> None:
        """Get the new device state."""
        await self.hub.send_packet({
            "title": MsgTitle.GET_PH_DATA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def set_ph_param(self, data: dict[str, Any]) -> None:
        """Send a SET_PH_PARAM packet, containing new values from data."""
        if self.ph_data is None:
            _LOGGER.error("set_ph_param: No PH_DATA packet received yet.")
            return
        await self.hub.send_packet({
            "title": self.ph_data["title"],
            "to": self.mac_address,
            "sollPH": self.ph_data["sollPH"],
            "active": self.ph_data["active"],
            "hystLow": self.ph_data["hystLow"],
            "hystHigh": self.ph_data["hystHigh"],
            "offset": self.ph_data["offset"],
            "acclimatization": self.ph_data["acclimatization"],
            "mode": self.ph_data["mode"],
            "expert": self.ph_data["expert"],
            "kH": self.ph_data["kH"],
            "schedule": self.ph_data["schedule"],
            "sync": self.ph_data["sync"],
            "partnerName": self.ph_data["partnerName"],
            "nightStartT": self.ph_data["nightStartT"],
            "dayStartT": self.ph_data["dayStartT"],
            "nReduce": self.ph_data["nReduce"],
            "from": "USER",
            **data,
        })

    @property
    def is_active(self) -> bool | None:
        """Return whether the device is active."""
        if self.ph_data is None:
            return None
        return bool(self.ph_data["active"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the filter should be active or not."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"active": int(active)})

    @property
    def is_ph(self) -> float | None:
        """Return the current pH value."""
        if self.ph_data is None:
            return None
        return self.ph_data["isPH"] / 10

    @property
    def soll_ph(self) -> float | None:
        """Return the desired pH value."""
        if self.ph_data is None:
            return None
        return self.ph_data["sollPH"] / 10

    async def set_soll_ph(self, value: float) -> None:
        """Set a new desired pH value."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"sollPH": int(value * 10)})

    @property
    def hyst_low(self) -> float | None:
        """Return the lower hysteresis threshold."""
        if self.ph_data is None:
            return None
        return self.ph_data["hystLow"] / 10

    async def set_hyst_low(self, value: float) -> None:
        """Set the lower hysteresis threshold."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"hystLow": int(value * 10)})

    @property
    def hyst_high(self) -> float | None:
        """Return the higher hysteresis threshold."""
        if self.ph_data is None:
            return None
        return self.ph_data["hystHigh"] / 10

    async def set_hyst_high(self, value: float) -> None:
        """Set the higher hysteresis threshold."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"hystHigh": int(value * 10)})

    @property
    def offset(self) -> float | None:
        """Return the offset value."""
        if self.ph_data is None:
            return None
        return self.ph_data["offset"] / 10

    async def set_offset(self, value: float) -> None:
        """Set the offset value."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"offset": int(value * 10)})

    @property
    def acclimatization(self) -> bool | None:
        """Return the acclimatization value."""
        if self.ph_data is None:
            return None
        return bool(self.ph_data["acclimatization"])

    async def set_acclimatization(self, *, value: bool) -> None:
        """Set the acclimatization value."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"acclimatization": int(value)})

    @property
    def mode(self) -> PHControlMode | None:
        """Return the pHControl mode."""
        if self.ph_data is None:
            return None
        return PHControlMode(self.ph_data["mode"])

    async def set_mode(self, value: PHControlMode) -> None:
        """Set the pHControl mode."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"mode": int(value)})

    @property
    def expert(self) -> bool | None:
        """Return whether expert mode is enabled for daycycle mode."""
        if self.ph_data is None:
            return None
        return bool(self.ph_data["expert"])

    async def set_expert(self, *, value: bool) -> None:
        """Set whether expert mode is enabled for daycycle mode."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"expert": int(value)})

    @property
    def kh(self) -> int | None:
        """Return the kH value in °dH."""
        if self.ph_data is None:
            return None
        return self.ph_data["kH"]

    @property
    def schedule(self) -> list[list[int]] | None:
        """Return the schedule for daycyle expert mode."""
        if self.ph_data is None:
            return None
        return self.ph_data["schedule"]

    async def set_schedule(self, schedule: list[list[int]]) -> None:
        """Set the schedule for daycyle expert mode."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"schedule": schedule})

    @property
    def sync(self) -> str | None:
        """Return the device MAC address to sync the daycycle mode."""
        if self.ph_data is None:
            return None
        return self.ph_data["sync"]

    async def set_sync(self, value: str) -> None:
        """Set the device MAC address to sync the daycycle mode."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"sync": value})

    @property
    def partner_name(self) -> str | None:
        """Return the name of the partner device."""
        if self.ph_data is None:
            return None
        return self.ph_data["partnerName"]

    async def set_partner_name(self, value: str) -> None:
        """Set the name of the partner device."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"partnerName": value})

    @property
    def day_start_time(self) -> time | None:
        """Return the day start time for Daycycle mode."""
        if self.ph_data is None:
            return None
        return time(
            self.ph_data["dayStartT"] // 60,
            self.ph_data["dayStartT"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_day_start_time(self, day_start_time: time) -> None:
        """Set the day start time for Daycycle mode."""
        if self.ph_data is None:
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
        await self.set_ph_param({"dayStartT": t.hour * 60 + t.minute})

    @property
    def night_start_time(self) -> time | None:
        """Return the night start time for Daycycle mode."""
        if self.ph_data is None:
            return None
        return time(
            self.ph_data["nightStartT"] // 60,
            self.ph_data["nightStartT"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_night_start_time(self, night_start_time: time) -> None:
        """Set the night start time for Daycycle mode."""
        if self.ph_data is None:
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
        await self.set_ph_param({"nightStartT": t.hour * 60 + t.minute})

    @property
    def night_temperature_offset(self) -> float | None:
        """Return the night temperature offset for Daycycle mode."""
        if self.ph_data is None:
            return None
        return self.ph_data["nReduce"] / 10

    async def set_night_temperature_offset(
        self, night_temperature_offset: float
    ) -> None:
        """Set the night temperature offset for Daycycle mode."""
        if self.ph_data is None:
            return
        await self.set_ph_param({"nReduce": int(night_temperature_offset * 10)})

    @property
    def alert_state(self) -> PHControlErrorCode | None:
        """Return the alert state."""
        if self.ph_data is None:
            return None
        return PHControlErrorCode(self.ph_data["alertState"])

    @property
    def service_time(self) -> int | None:
        """Return the remaining days until the electrode has to be calibrated."""
        if self.ph_data is None:
            return None
        return self.ph_data["serviceTime"]

    @property
    def valve_is_active(self) -> bool | None:
        """Return whether the valve is active."""
        if self.ph_data is None:
            return None
        return bool(self.ph_data["valveIsActive"])

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "ph_data": self.ph_data,
            **super().as_dict(),
        }
