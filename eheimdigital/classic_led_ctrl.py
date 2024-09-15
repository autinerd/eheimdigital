"""The EHEIM classicLEDcontrol light controller."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from eheimdigital.device import EheimDigitalDevice
from eheimdigital.types import (
    CCVPacket,
    CloudPacket,
    MoonPacket,
    MsgTitle,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub


class EheimDigitalClassicLEDControl(EheimDigitalDevice):
    """Represent a EHEIM classicLEDcontrol light controller."""

    ccv: CCVPacket
    cloud: CloudPacket
    moon: MoonPacket
    tankconfig: list[list[str]]
    power: list[list[int]]

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a classicLEDcontrol light controller."""
        super().__init__(hub, usrdta)
        self.tankconfig = json.loads(usrdta["tankconfig"])
        self.power = json.loads(usrdta["power"])

    async def parse_message(self, msg: dict) -> None:
        """Parse a message."""
        match msg["title"]:
            case MsgTitle.CCV:
                self.ccv = CCVPacket(**msg)
            case MsgTitle.CLOUD:
                self.cloud = CloudPacket(**msg)
            case MsgTitle.MOON:
                self.moon = MoonPacket(**msg)

    async def update(self) -> None:
        """Get the new light state."""
        await self.hub.send_packet(
            {"title": "REQ_CCV", "to": self.mac_address, "from": "USER"}
        )
        if "moon" not in self.__dict__:
            await self.hub.send_packet(
                {"title": "GET_MOON", "to": self.mac_address, "from": "USER"}
            )
        if "cloud" not in self.__dict__:
            await self.hub.send_packet(
                {"title": "GET_CLOUD", "to": self.mac_address, "from": "USER"}
            )

    @property
    def light_level(self) -> tuple[int | None, int | None]:
        """Return the current light level of the channels."""
        return (
            self.ccv["currentValues"][0] if len(self.tankconfig[0]) > 0 else None,
            self.ccv["currentValues"][1] if len(self.tankconfig[1]) > 0 else None,
        )

    @property
    def power_consumption(self) -> tuple[float | None, float | None]:
        """Return the power consumption of the channels."""
        return (
            sum(self.power[0]) * self.ccv["currentValues"][0]
            if len(self.tankconfig[0]) > 0
            else None,
            sum(self.power[1]) * self.ccv["currentValues"][1]
            if len(self.tankconfig[1]) > 0
            else None,
        )
