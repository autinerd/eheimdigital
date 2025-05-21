"""The EHEIM classicLEDcontrol light controller."""

from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from eheimdigital.device import EheimDigitalDevice
from eheimdigital.types import (
    AcclimatePacket,
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
    acclimate: AcclimatePacket | None = None
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
            case MsgTitle.ACCLIMATE:
                self.acclimate = AcclimatePacket(**msg)
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
        if "acclimate" not in self.__dict__:
            await self.hub.send_packet({
                "title": "GET_ACCL",
                "to": self.mac_address,
                "from": "USER",
            })

    async def set_cloud(self, data: dict[str, Any]) -> None:
        """Set the cloud data."""
        if self.cloud is None:
            _LOGGER.error("set_cloud: No CLOUD packet received yet.")
            return
        await self.hub.send_packet({
            "title": MsgTitle.CLOUD,
            "to": self.mac_address,
            "from": "USER",
            "probability": self.cloud["probability"],
            "maxAmount": self.cloud["maxAmount"],
            "minIntensity": self.cloud["minIntensity"],
            "maxIntensity": self.cloud["maxIntensity"],
            "minDuration": self.cloud["minDuration"],
            "maxDuration": self.cloud["maxDuration"],
            "cloudActive": self.cloud["cloudActive"],
            "mode": self.cloud["mode"],
            **data,
        })

    async def set_moon(self, data: dict[str, Any]) -> None:
        """Set the moon data."""
        if self.moon is None:
            _LOGGER.error("set_moon: No MOON packet received yet.")
            return
        await self.hub.send_packet({
            "title": MsgTitle.MOON,
            "to": self.mac_address,
            "from": "USER",
            "maxmoonlight": self.moon["maxmoonlight"],
            "minmoonlight": self.moon["minmoonlight"],
            "moonlightActive": self.moon["moonlightActive"],
            "moonlightCycle": self.moon["moonlightCycle"],
            **data,
        })

    async def set_acclimate(self, data: dict[str, Any]) -> None:
        """Set the acclimate data."""
        if self.acclimate is None:
            _LOGGER.error("set_acclimate: No ACCLIMATE packet received yet.")
            return
        await self.hub.send_packet({
            "title": MsgTitle.ACCLIMATE,
            "to": self.mac_address,
            "from": "USER",
            "duration": self.acclimate["duration"],
            "intensityReduction": self.acclimate["intensityReduction"],
            "currentAcclDay": self.acclimate["currentAcclDay"],
            "acclActive": self.acclimate["acclActive"],
            "pause": self.acclimate["pause"],
            **data,
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

    @property
    def cloud_probability(self) -> int | None:
        """Return the cloud probability."""
        if self.cloud is None:
            return None
        return self.cloud["probability"]

    async def set_cloud_probability(self, probability: int) -> None:
        """Set the cloud probability."""
        if self.cloud is None:
            return
        await self.set_cloud({"probability": probability})

    @property
    def cloud_max_amount(self) -> int | None:
        """Return the maximum amount of clouds."""
        if self.cloud is None:
            return None
        return self.cloud["maxAmount"]

    async def set_cloud_max_amount(self, max_amount: int) -> None:
        """Set the maximum amount of clouds."""
        if self.cloud is None:
            return
        await self.set_cloud({"maxAmount": max_amount})

    @property
    def cloud_min_intensity(self) -> int | None:
        """Return the minimum intensity of clouds."""
        if self.cloud is None:
            return None
        return self.cloud["minIntensity"]

    async def set_cloud_min_intensity(self, min_intensity: int) -> None:
        """Set the minimum intensity of clouds."""
        if self.cloud is None:
            return
        await self.set_cloud({"minIntensity": min_intensity})

    @property
    def cloud_max_intensity(self) -> int | None:
        """Return the maximum intensity of clouds."""
        if self.cloud is None:
            return None
        return self.cloud["maxIntensity"]

    async def set_cloud_max_intensity(self, max_intensity: int) -> None:
        """Set the maximum intensity of clouds."""
        if self.cloud is None:
            return
        await self.set_cloud({"maxIntensity": max_intensity})

    @property
    def cloud_min_duration(self) -> int | None:
        """Return the minimum cloud duration."""
        if self.cloud is None:
            return None
        return self.cloud["minDuration"]

    async def set_cloud_min_duration(self, min_duration: int) -> None:
        """Set the minimum cloud duration."""
        if self.cloud is None:
            return
        await self.set_cloud({"minDuration": min_duration})

    @property
    def cloud_max_duration(self) -> int | None:
        """Return the maximum cloud duration."""
        if self.cloud is None:
            return None
        return self.cloud["maxDuration"]

    async def set_cloud_max_duration(self, max_duration: int) -> None:
        """Set the maximum cloud duration."""
        if self.cloud is None:
            return
        await self.set_cloud({"maxDuration": max_duration})

    @property
    def cloud_active(self) -> bool | None:
        """Return whether the cloud effect is active."""
        if self.cloud is None:
            return None
        return bool(self.cloud["cloudActive"])

    async def set_cloud_active(self, *, active: bool) -> None:
        """Set whether the cloud effect is active."""
        if self.cloud is None:
            return
        await self.set_cloud({"cloudActive": int(active)})

    @property
    def cloud_mode(self) -> int | None:
        """Return the cloud mode."""
        if self.cloud is None:
            return None
        return self.cloud["mode"]

    async def set_cloud_mode(self, mode: int) -> None:
        """Set the cloud mode."""
        if self.cloud is None:
            return
        await self.set_cloud({"mode": mode})

    @property
    def moon_max_light(self) -> int | None:
        """Return the maximum moonlight intensity."""
        if self.moon is None:
            return None
        return self.moon["maxmoonlight"]

    async def set_moon_max_light(self, max_light: int) -> None:
        """Set the maximum moonlight intensity."""
        if self.moon is None:
            return
        await self.set_moon({"maxmoonlight": max_light})

    @property
    def moon_min_light(self) -> int | None:
        """Return the minimum moonlight intensity."""
        if self.moon is None:
            return None
        return self.moon["minmoonlight"]

    async def set_moon_min_light(self, min_light: int) -> None:
        """Set the minimum moonlight intensity."""
        if self.moon is None:
            return
        await self.set_moon({"minmoonlight": min_light})

    @property
    def moon_light_active(self) -> bool | None:
        """Return whether the moonlight effect is active."""
        if self.moon is None:
            return None
        return bool(self.moon["moonlightActive"])

    async def set_moon_light_active(self, *, active: bool) -> None:
        """Set whether the moonlight effect is active."""
        if self.moon is None:
            return
        await self.set_moon({"moonlightActive": int(active)})

    @property
    def moon_light_cycle(self) -> bool | None:
        """Return whether the moonlight cycle is active."""
        if self.moon is None:
            return None
        return bool(self.moon["moonlightCycle"])

    async def set_moon_light_cycle(self, *, cycle: bool) -> None:
        """Set whether the moonlight cycle is active."""
        if self.moon is None:
            return
        await self.set_moon({"moonlightCycle": int(cycle)})

    @property
    def acclimate_duration(self) -> int | None:
        """Return the acclimate duration."""
        if self.acclimate is None:
            return None
        return self.acclimate["duration"]

    async def set_acclimate_duration(self, duration: int) -> None:
        """Set the acclimate duration."""
        if self.acclimate is None:
            return
        await self.set_acclimate({"duration": duration})

    @property
    def acclimate_intensity_reduction(self) -> int | None:
        """Return the acclimate intensity reduction."""
        if self.acclimate is None:
            return None
        return self.acclimate["intensityReduction"]

    async def set_acclimate_intensity_reduction(self, reduction: int) -> None:
        """Set the acclimate intensity reduction."""
        if self.acclimate is None:
            return
        await self.set_acclimate({"intensityReduction": reduction})

    @property
    def acclimate_current_day(self) -> int | None:
        """Return the current acclimate day."""
        if self.acclimate is None:
            return None
        return self.acclimate["currentAcclDay"]

    async def set_acclimate_current_day(self, day: int) -> None:
        """Set the current acclimate day."""
        if self.acclimate is None:
            return
        await self.set_acclimate({"currentAcclDay": day})

    @property
    def acclimate_active(self) -> bool | None:
        """Return whether the acclimate effect is active."""
        if self.acclimate is None:
            return None
        return bool(self.acclimate["acclActive"])

    async def set_acclimate_active(self, *, active: bool) -> None:
        """Set whether the acclimate effect is active."""
        if self.acclimate is None:
            return
        await self.set_acclimate({"acclActive": int(active)})

    @property
    def acclimate_pause(self) -> bool | None:
        """Return whether the acclimate effect is paused."""
        if self.acclimate is None:
            return None
        return bool(self.acclimate["pause"])

    async def set_acclimate_pause(self, *, pause: bool) -> None:
        """Set whether the acclimate effect is paused."""
        if self.acclimate is None:
            return
        await self.set_acclimate({"pause": int(pause)})

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "ccv": self.ccv,
            "clock": self.clock,
            "cloud": self.cloud,
            "moon": self.moon,
            "acclimate": self.acclimate,
            **super().as_dict(),
        }
