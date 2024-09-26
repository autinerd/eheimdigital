"""The EHEIM classicLEDcontrol light controller."""

from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from eheimdigital.device import EheimDigitalDevice
from eheimdigital.types import (
    CCVPacket,
    ClockPacket,
    CloudPacket,
    LightMode,
    MoonPacket,
    MsgTitle,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalClassicLEDControl(EheimDigitalDevice):
    """Represent a EHEIM classicLEDcontrol light controller."""

    ccv: CCVPacket | None = None
    clock: ClockPacket | None = None
    cloud: CloudPacket | None = None
    moon: MoonPacket | None = None
    tankconfig: list[list[str]]
    power: list[list[int]]

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a classicLEDcontrol light controller."""
        super().__init__(hub, usrdta)
        self.tankconfig = json.loads(usrdta["tankconfig"])
        self.power = json.loads(usrdta["power"])

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        match msg["title"]:
            case MsgTitle.CCV:
                self.ccv = CCVPacket(**msg)
            case MsgTitle.CLOUD:
                self.cloud = CloudPacket(**msg)
            case MsgTitle.MOON:
                self.moon = MoonPacket(**msg)
            case MsgTitle.CLOCK:
                self.clock = ClockPacket(**msg)
            case _:
                pass

    @override
    async def update(self) -> None:
        """Get the new light state."""
        await self.hub.send_packet({
            "title": "REQ_CCV",
            "to": self.mac_address,
            "from": "USER",
        })
        await self.hub.send_packet({
            "title": "GET_CLOCK",
            "to": self.mac_address,
            "from": "USER",
        })
        if "moon" not in self.__dict__:
            await self.hub.send_packet({
                "title": "GET_MOON",
                "to": self.mac_address,
                "from": "USER",
            })
        if "cloud" not in self.__dict__:
            await self.hub.send_packet({
                "title": "GET_CLOUD",
                "to": self.mac_address,
                "from": "USER",
            })

    @property
    def light_level(self) -> tuple[int | None, int | None]:
        """Return the current light level of the channels."""
        if self.ccv is None:
            return (None, None)
        return (
            self.ccv["currentValues"][0] if len(self.tankconfig[0]) > 0 else None,
            self.ccv["currentValues"][1] if len(self.tankconfig[1]) > 0 else None,
        )

    @property
    def power_consumption(self) -> tuple[float | None, float | None]:
        """Return the power consumption of the channels."""
        if self.ccv is None:
            return (None, None)
        return (
            sum(self.power[0]) * self.ccv["currentValues"][0]
            if len(self.tankconfig[0]) > 0
            else None,
            sum(self.power[1]) * self.ccv["currentValues"][1]
            if len(self.tankconfig[1]) > 0
            else None,
        )

    @property
    def light_mode(self) -> LightMode | None:
        """Return the current light operation mode."""
        if self.clock is None or "mode" not in self.clock:
            return None
        return LightMode(self.clock["mode"])

    async def set_light_mode(self, mode: LightMode) -> None:
        """Set the light operation mode."""
        await self.hub.send_packet({
            "title": str(mode),
            "to": self.mac_address,
            "from": "USER",
        })

    async def turn_on(self, value: int, channel: int) -> None:
        """Set a new brightness value for a channel."""
        if self.light_mode == LightMode.DAYCL_MODE:
            await self.set_light_mode(LightMode.MAN_MODE)
        if self.ccv is None:
            return
        currentvalues = self.ccv["currentValues"]
        currentvalues[channel] = value
        await self.hub.send_packet({
            "title": "CCV-SL",
            "currentValues": currentvalues,
            "to": self.mac_address,
            "from": "USER",
        })

    async def turn_off(self, channel: int) -> None:
        """Turn off a channel."""
        if self.light_mode == LightMode.DAYCL_MODE:
            await self.set_light_mode(LightMode.MAN_MODE)
        if self.ccv is None:
            return
        currentvalues = self.ccv["currentValues"]
        currentvalues[channel] = 0
        await self.hub.send_packet({
            "title": "CCV-SL",
            "currentValues": currentvalues,
            "to": self.mac_address,
            "from": "USER",
        })
