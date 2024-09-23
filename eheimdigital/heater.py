"""The Eheim Digital Heater."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .device import EheimDigitalDevice
from .types import (
    HeaterDataPacket,
    HeaterMode,
    HeaterUnit,
    MsgTitle,
)

if TYPE_CHECKING:
    from .hub import EheimDigitalHub
    from .types import UsrDtaPacket


class EheimDigitalHeater(EheimDigitalDevice):
    """Represent a Eheim Digital Heater."""

    heater_data: HeaterDataPacket

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a heater."""
        super().__init__(hub, usrdta)

    async def parse_message(self, msg: dict) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.HEATER_DATA:
            self.heater_data = HeaterDataPacket(**msg)

    async def update(self) -> None:
        """Get the new heater state."""
        await self.hub.send_packet(
            {"title": MsgTitle.GET_EHEATER_DATA, "to": self.mac_address, "from": "USER"}
        )

    async def set_eheater_param(self, data: dict) -> None:
        """Send a SET_EHEATER_PARAM packet, containing new values from data."""
        await self.hub.send_packet(
            {
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
            }
        )

    @property
    def temperature_unit(self) -> HeaterUnit:
        """Return the temperature unit."""
        return HeaterUnit(self.heater_data["mUnit"])

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self.heater_data["isTemp"] / 10

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self.heater_data["sollTemp"] / 10

    async def set_target_temperature(self, value: float) -> None:
        """Set a new target temperature."""
        await self.set_eheater_param({"sollTemp": int(value * 10)})

    @property
    def temperature_offset(self) -> float:
        """Return the temperature offset."""
        return self.heater_data["offset"] / 10

    async def set_temperature_offset(self, value: float) -> None:
        """Set a temperature offset."""
        await self.set_eheater_param({"offset": int(value * 10)})

    @property
    def operation_mode(self) -> HeaterMode:
        """Return the heater operation mode."""
        return HeaterMode(self.heater_data["mode"])

    @property
    def is_heating(self) -> bool:
        """Return whether the heater is heating."""
        return bool(self.heater_data["isHeating"])
