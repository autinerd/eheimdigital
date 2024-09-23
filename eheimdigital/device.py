"""The Eheim Digital device."""

from __future__ import annotations

from abc import abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

from .types import EheimDeviceType

if TYPE_CHECKING:
    from .hub import EheimDigitalHub
    from .types import UsrDtaPacket


class EheimDigitalDevice:
    """Represent a Eheim Digital device."""

    hub: EheimDigitalHub
    usrdta: UsrDtaPacket

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a device."""
        self.hub = hub
        self.usrdta = usrdta

    @cached_property
    def name(self) -> str:
        """Device name."""
        return self.usrdta["name"]

    @cached_property
    def mac_address(self) -> str:
        """Device MAC address."""
        return self.usrdta["from"]

    @cached_property
    def sw_version(self) -> str:
        """Device software version."""
        return f"{self.usrdta["revision"][0]//1000}.{(self.usrdta["revision"][0]%1000)//100}.{self.usrdta["revision"][0]%100}_{self.usrdta["revision"][1]//1000}.{(self.usrdta["revision"][1]%1000)//100}.{self.usrdta["revision"][1]%100}"

    @cached_property
    def device_type(self) -> EheimDeviceType:
        """Device type."""
        return EheimDeviceType(self.usrdta["version"])

    @cached_property
    def aquarium_name(self) -> str:
        """Aquarium name."""
        return self.usrdta["aqName"]

    @abstractmethod
    async def parse_message(self, msg: dict) -> None:
        """Parse a message."""

    @abstractmethod
    async def update(self) -> None:
        """Update a device state."""