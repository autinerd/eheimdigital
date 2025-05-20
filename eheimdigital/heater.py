"""The Eheim Digital Heater."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import TYPE_CHECKING, Any, override

from .device import EheimDigitalDevice
from .types import HeaterDataPacket, HeaterMode, HeaterUnit, MsgTitle

if TYPE_CHECKING:
    from .hub import EheimDigitalHub
    from .types import UsrDtaPacket


class EheimDigitalHeater(EheimDigitalDevice):
    """Represent a Eheim Digital Heater."""

    heater_data: HeaterDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a heater."""
        super().__init__(hub, usrdta)

    @override
    async def parse_message(self, msg: dict) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.HEATER_DATA:
            self.heater_data = HeaterDataPacket(**msg)

    @override
    async def update(self) -> None:
        """Get the new heater state."""
        await self.hub.send_packet({
            "title": MsgTitle.GET_EHEATER_DATA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def set_eheater_param(self, data: dict[str, Any]) -> None:
        """Send a SET_EHEATER_PARAM packet, containing new values from data."""
        if self.heater_data is None:
            return
        await self.hub.send_packet({
            "title": "SET_EHEATER_PARAM",
            "to": self.heater_data["from"],
            "mUnit": self.heater_data["mUnit"],
            "sollTemp": self.heater_data["sollTemp"],
            "active": self.heater_data["active"],
            "hystLow": self.heater_data["hystLow"],
            "hystHigh": self.heater_data["hystHigh"],
            "offset": self.heater_data["offset"],
            "mode": self.heater_data["mode"],
            "sync": self.heater_data["sync"],
            "partnerName": self.heater_data["partnerName"],
            "dayStartT": self.heater_data["dayStartT"],
            "nightStartT": self.heater_data["nightStartT"],
            "nReduce": self.heater_data["nReduce"],
            "from": "USER",
            **data,
        })

    @property
    def temperature_unit(self) -> HeaterUnit | None:
        """Return the temperature unit."""
        if self.heater_data is None:
            return None
        return HeaterUnit(self.heater_data["mUnit"])

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.heater_data is None:
            return None
        return self.heater_data["isTemp"] / 10

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self.heater_data is None:
            return None
        return self.heater_data["sollTemp"] / 10

    async def set_target_temperature(self, value: float) -> None:
        """Set a new target temperature."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({"sollTemp": int(value * 10)})

    @property
    def hysteresis(self) -> tuple[float, float] | None:
        """Return the hysteresis for turning on and off the heater."""
        if self.heater_data is None:
            return None
        return (self.heater_data["hystLow"] / 10, self.heater_data["hystHigh"] / 10)

    async def set_hysteresis(self, hyst_low: float, hyst_high: float) -> None:
        """Set the hysteresis for turning on and off the heater."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({
            "hystLow": int(hyst_low * 10),
            "hystHigh": int(hyst_high * 10),
        })

    @property
    def temperature_offset(self) -> float | None:
        """Return the temperature offset."""
        if self.heater_data is None:
            return None
        return self.heater_data["offset"] / 10

    async def set_temperature_offset(self, value: float) -> None:
        """Set a temperature offset."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({"offset": int(value * 10)})

    @property
    def operation_mode(self) -> HeaterMode | None:
        """Return the heater operation mode."""
        if self.heater_data is None:
            return None
        return HeaterMode(self.heater_data["mode"])

    async def set_operation_mode(self, mode: HeaterMode) -> None:
        """Set the heater operation mode."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({"mode": int(mode)})

    @property
    def is_heating(self) -> bool | None:
        """Return whether the heater is heating."""
        if self.heater_data is None:
            return None
        return bool(self.heater_data["isHeating"])

    @property
    def is_active(self) -> bool | None:
        """Return whether the heater is enabled."""
        if self.heater_data is None:
            return None
        return bool(self.heater_data["active"])

    async def set_active(self, *, active: bool) -> None:
        """Set whether the heater should be active or not."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({"active": int(active)})

    @property
    def partner_device(self) -> EheimDigitalDevice | str | None:
        """Return the partner device in Smart mode. If the device is not known, return the MAC address."""
        if self.heater_data is None or not self.heater_data["sync"]:
            return None
        if self.heater_data["sync"] in self.hub.devices:
            return self.hub.devices[self.heater_data["sync"]]
        return self.heater_data["sync"]

    async def set_partner_device(self, partner_device: EheimDigitalDevice) -> None:
        """Set the partner device for Smart mode."""
        if self.heater_data is None or not partner_device.mac_address:
            return
        await self.set_eheater_param({
            "partnerName": partner_device.name,
            "sync": partner_device.mac_address,
        })

    @property
    def night_temperature_offset(self) -> float | None:
        """Return the night temperature offset for Bio mode."""
        if self.heater_data is None:
            return None
        return self.heater_data["nReduce"] / 10

    async def set_night_temperature_offset(
        self, night_temperature_offset: float
    ) -> None:
        """Set the night temperature offset for Bio mode."""
        if self.heater_data is None:
            return
        await self.set_eheater_param({"nReduce": int(night_temperature_offset * 10)})

    @property
    def day_start_time(self) -> time | None:
        """Return the day start time for Bio mode."""
        if self.heater_data is None:
            return None
        return time(
            self.heater_data["dayStartT"] // 60,
            self.heater_data["dayStartT"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_day_start_time(self, day_start_time: time) -> None:
        """Set the day start time for Bio mode."""
        if self.heater_data is None:
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
        await self.set_eheater_param({"dayStartT": t.hour * 60 + t.minute})

    @property
    def night_start_time(self) -> time | None:
        """Return the night start time for Bio mode."""
        if self.heater_data is None:
            return None
        return time(
            self.heater_data["nightStartT"] // 60,
            self.heater_data["nightStartT"] % 60,
            tzinfo=timezone(timedelta(minutes=self.usrdta["timezone"])),
        )

    async def set_night_start_time(self, night_start_time: time) -> None:
        """Set the night start time for Bio mode."""
        if self.heater_data is None:
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
        await self.set_eheater_param({"nightStartT": t.hour * 60 + t.minute})

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "heater_data": self.heater_data,
            **super().as_dict(),
        }
