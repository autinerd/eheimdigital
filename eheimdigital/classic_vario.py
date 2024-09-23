"""The Eheim Digital classicVARIO filter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from .device import EheimDigitalDevice
from .types import (
    ClassicVarioDataPacket,
    FilterMode,
    MsgTitle,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from eheimdigital.hub import EheimDigitalHub

_LOGGER = getLogger(__package__)


class EheimDigitalClassicVario(EheimDigitalDevice):
    """Represent a Eheim Digital classicVARIO filter."""

    classic_vario_data: ClassicVarioDataPacket | None = None

    def __init__(self, hub: EheimDigitalHub, usrdta: UsrDtaPacket) -> None:
        """Initialize a classicVARIO filter."""
        super().__init__(hub, usrdta)

    async def parse_message(self, msg: dict) -> None:
        """Parse a message."""
        if msg["title"] == MsgTitle.CLASSIC_VARIO_DATA:
            self.classic_vario_data = ClassicVarioDataPacket(**msg)

    async def update(self) -> None:
        """Get the new filter state."""
        await self.hub.send_packet(
            {
                "title": MsgTitle.GET_CLASSIC_VARIO_DATA,
                "to": self.mac_address,
                "from": "USER",
            }
        )

    async def set_classic_vario_param(self, data: dict) -> None:
        """Send a SET_CLASSIC_VARIO_PARAM packet, containing new values from data."""
        if self.classic_vario_data is None:
            _LOGGER.error(
                "set_classic_vario_param: No CLASSIC_VARIO_DATA packet received yet."
            )
            return
        await self.hub.send_packet(
            {
                "title": "SET_CLASSIC_VARIO_PARAM",
                "to": self.classic_vario_data["from"],
                "filterActive": self.classic_vario_data["filterActive"],
                "rel_manual_motor_speed": self.classic_vario_data[
                    "rel_manual_motor_speed"
                ],
                "rel_motor_speed_day": self.classic_vario_data["rel_motor_speed_day"],
                "rel_motor_speed_night": self.classic_vario_data[
                    "rel_motor_speed_night"
                ],
                "startTime_day": self.classic_vario_data["startTime_day"],
                "startTime_night": self.classic_vario_data["startTime_night"],
                "pulse_motorSpeed_High": self.classic_vario_data[
                    "pulse_motorSpeed_High"
                ],
                "pulse_motorSpeed_Low": self.classic_vario_data["pulse_motorSpeed_Low"],
                "pulse_Time_High": self.classic_vario_data["pulse_Time_High"],
                "pulse_Time_Low": self.classic_vario_data["pulse_Time_Low"],
                "pumpMode": self.classic_vario_data["pumpMode"],
                "from": "USER",
                **data,
            }
        )

    @property
    def current_speed(self) -> int:
        """Return the current filter pump speed."""
        return self.classic_vario_data["rel_speed"]

    @property
    def service_hours(self) -> int:
        """Return the amount of hours until the next service is needed."""
        return self.classic_vario_data["serviceHour"]

    @property
    def filter_mode(self) -> FilterMode:
        """Return the current filter mode."""
        return FilterMode(self.classic_vario_data["pumpMode"])

    async def set_filter_mode(self, value: FilterMode) -> None:
        """Set the filter mode."""
        await self.set_classic_vario_param({"pumpMode": value.value})

    @property
    def is_active(self) -> bool:
        """Return whether the filter is active."""
        return bool(self.classic_vario_data["filterActive"])
