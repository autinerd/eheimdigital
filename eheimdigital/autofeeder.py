"""The EHEIM autofeeder+ auto feeder."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any, override

from eheimdigital.device import EheimDigitalDevice
from eheimdigital.types import FeederDataPacket, FeederDrumState, MsgTitle, UsrDtaPacket

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalAutofeeder(EheimDigitalDevice):
    """EHEIM autofeeder+ auto feeder."""

    feeder_data: FeederDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize the EHEIM autofeeder+ auto feeder."""
        super().__init__(hub, usrdta)

    @override
    async def parse_message(self, msg: dict[str, Any]) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.FEEDER_DATA:
            self.feeder_data = FeederDataPacket(**msg)

    @override
    async def update(self) -> None:
        """Get the new feeder state."""
        await self.hub.send_packet({
            "title": MsgTitle.GET_FEEDER_DATA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def set_feeder_data(self, data: dict[str, Any]) -> None:
        """Send a SET_FEEDER_DATA packet, containing new values from data."""
        if self.feeder_data is None:
            _LOGGER.error("set_feeder_data: No FEEDER_DATA packet received yet.")
            return
        await self.hub.send_packet({
            "title": MsgTitle.SET_FEEDER_DATA,
            "to": self.mac_address,
            "from": "USER",
            "configuration": self.feeder_data["configuration"],
            "overfeeding": self.feeder_data["overfeeding"],
            "sync": self.feeder_data["sync"],
            "partnerName": self.feeder_data["partnerName"],
            "sollRegulation": self.feeder_data["sollRegulation"],
            "feedingBreak": self.feeder_data["feedingBreak"],
            "breakDay": self.feeder_data["breakDay"],
            **data,
        })

    async def set_feeder_full(self) -> None:
        """Set the feeder drum to full."""
        await self.hub.send_packet({
            "title": MsgTitle.SET_FEEDER_FULL,
            "to": self.mac_address,
            "from": "USER",
        })

    async def set_feeder_tara(self) -> None:
        """Set the current drum weight as tara."""
        await self.hub.send_packet({
            "title": MsgTitle.SET_FEEDER_TARA,
            "to": self.mac_address,
            "from": "USER",
        })

    async def manual_measurement(self) -> None:
        """Start a manual drum weight measurement."""
        await self.hub.send_packet({
            "title": MsgTitle.SET_MANUAL_MEASUREMENT,
            "to": self.mac_address,
            "from": "USER",
        })

    async def stop_feeder_sync(self) -> None:
        """Stop the feeder sync."""
        await self.hub.send_packet({
            "title": MsgTitle.SET_STOP_FEEDER_SYNC,
            "to": self.mac_address,
            "from": "USER",
        })

    @property
    def weight(self) -> float | None:
        """Get the weight of the feeder content in grams."""
        if self.feeder_data is None:
            return None
        return self.feeder_data["weight"]

    @property
    def is_spinning(self) -> bool | None:
        """Get the spinning state of the feeder."""
        if self.feeder_data is None:
            return None
        return bool(self.feeder_data["isSpinning"])

    @property
    def level(self) -> tuple[int, FeederDrumState] | None:
        """Get the level of the feeder drum."""
        if self.feeder_data is None:
            return None
        return (
            self.feeder_data["level"][0],
            FeederDrumState(self.feeder_data["level"][1]),
        )

    @property
    def configuration(self) -> list[list[int]] | None:
        """Get the configuration of the feeder."""
        if self.feeder_data is None:
            return None
        return self.feeder_data["configuration"]

    async def set_configuration(self, configuration: list[list[int]]) -> None:
        """Set the configuration of the feeder."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "configuration": configuration,
        })

    @property
    def overfeeding(self) -> bool | None:
        """Get whether the overfeeding protection is enabled."""
        if self.feeder_data is None:
            return None
        return bool(self.feeder_data["overfeeding"])

    async def set_overfeeding(self, *, overfeeding: bool) -> None:
        """Set the overfeeding protection."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "overfeeding": int(overfeeding),
        })

    @property
    def sync(self) -> str | None:
        """Get the synced device address."""
        if self.feeder_data is None:
            return None
        return self.feeder_data["sync"]

    async def set_sync(self, sync: str) -> None:
        """Set the synced device address."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "sync": sync,
        })

    @property
    def partner_name(self) -> str | None:
        """Get the name of the synced device."""
        if self.feeder_data is None:
            return None
        return self.feeder_data["partnerName"]

    async def set_partner_name(self, partner_name: str) -> None:
        """Set the name of the synced device."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "partnerName": partner_name,
        })

    @property
    def soll_regulation(self) -> bool | None:
        """Get whether the filter speed regulation is enabled."""
        if self.feeder_data is None:
            return None
        return bool(self.feeder_data["sollRegulation"])

    async def set_soll_regulation(self, *, soll_regulation: bool) -> None:
        """Set the filter speed regulation."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "sollRegulation": int(soll_regulation),
        })

    @property
    def feeding_break(self) -> bool | None:
        """Get whether the random feeding break is enabled."""
        if self.feeder_data is None:
            return None
        return bool(self.feeder_data["feedingBreak"])

    async def set_feeding_break(self, *, feeding_break: bool) -> None:
        """Set the random feeding break."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "feedingBreak": int(feeding_break),
        })

    @property
    def break_day(self) -> bool | None:
        """Get whether today is a break day."""
        if self.feeder_data is None:
            return None
        return bool(self.feeder_data["breakDay"])

    async def set_break_day(self, *, break_day: bool) -> None:
        """Set today as a break day."""
        if self.feeder_data is None:
            return
        await self.set_feeder_data({
            "breakDay": int(break_day),
        })

    @override
    def as_dict(self) -> dict[str, Any]:
        """Return the device as a dictionary."""
        return {
            "feeder_data": self.feeder_data,
            **super().as_dict(),
        }
