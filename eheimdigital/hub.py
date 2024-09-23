"""The Eheim Digital hub."""

from __future__ import annotations

import asyncio
import typing
from logging import getLogger

import aiohttp

from .classic_led_ctrl import EheimDigitalClassicLEDControl
from .classic_vario import EheimDigitalClassicVario
from .heater import EheimDigitalHeater
from .types import EheimDeviceType, MeshNetworkPacket, MsgTitle, UsrDtaPacket

if typing.TYPE_CHECKING:
    from .device import EheimDigitalDevice


_LOGGER = getLogger(__package__)


class EheimDigitalHub:
    """Represent a Eheim Digital hub."""

    devices: dict[str, EheimDigitalDevice]
    ws: aiohttp.ClientWebSocketResponse
    receive_task: asyncio.Task
    loop: asyncio.AbstractEventLoop
    receive_callback: typing.Callable[[], typing.Awaitable[None]] | None
    master: EheimDigitalDevice | None

    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        receive_callback: typing.Callable[[], typing.Awaitable[None]] | None = None,
    ) -> None:
        """Initialize a hub."""
        self.session = session or aiohttp.ClientSession(
            base_url="http://eheimdigital.local"
        )
        self.devices = {}
        self.loop = loop or asyncio.get_event_loop()
        self.receive_callback = receive_callback
        self.master = None

    async def connect(self) -> None:  # pragma: no cover
        """Connect to the hub."""
        self.ws = await self.session.ws_connect("/ws")
        self.receive_task = self.loop.create_task(self.receive_messages())

    async def close(self) -> None:  # pragma: no cover
        """Close the connection."""
        self.receive_task.cancel()
        if self.ws is not None and not self.ws.closed:
            await self.ws.close()

    def add_device(self, usrdta: UsrDtaPacket) -> None:
        """Add a device to the device list."""
        match EheimDeviceType(usrdta["version"]):
            case EheimDeviceType.VERSION_EHEIM_EXT_HEATER:
                self.devices[usrdta["from"]] = EheimDigitalHeater(self, usrdta)
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_VARIO:
                self.devices[usrdta["from"]] = EheimDigitalClassicVario(self, usrdta)
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_LED_CTRL_PLUS_E:
                self.devices[usrdta["from"]] = EheimDigitalClassicLEDControl(
                    self, usrdta
                )
        if self.master is None and usrdta["from"] in self.devices:
            self.master = self.devices[usrdta["from"]]

    async def request_usrdta(self, mac_address: str) -> None:
        """Request the USRDTA of a device."""
        await self.send_packet(
            {"title": MsgTitle.GET_USRDTA, "to": mac_address, "from": "USER"}
        )

    async def send_packet(self, packet: dict) -> None:
        """Send a packet to the hub."""
        await self.ws.send_json(packet)

    async def parse_mesh_network(self, msg: MeshNetworkPacket) -> None:
        """Parse a MESH_NETWORK packet."""
        for client in msg["clientList"]:
            if client not in self.devices:
                await self.request_usrdta(client)

    async def parse_usrdta(self, msg: UsrDtaPacket) -> None:
        """Parse a USRDTA packet."""
        if msg["from"] not in self.devices:
            self.add_device(msg)

    async def parse_message(self, msg: dict) -> None:
        """Parse a received message."""
        if "from" not in msg:
            _LOGGER.debug("Received message without 'from' property: %s", msg)
            return
        if "USER" in msg["from"]:
            _LOGGER.debug("Received message from other user: %s", msg)
            return
        if "title" not in msg:
            _LOGGER.debug("Received message without 'title' property: %s", msg)
            return
        match msg["title"]:
            case MsgTitle.MESH_NETWORK:
                _LOGGER.debug("Received mesh network packet: %s", msg)
                await self.parse_mesh_network(MeshNetworkPacket(**msg))
            case MsgTitle.USRDTA:
                _LOGGER.debug("Received usrdta packet: %s", msg)
                await self.parse_usrdta(UsrDtaPacket(**msg))
                if self.receive_callback:
                    await self.receive_callback()
            case _:
                _LOGGER.debug(
                    "Received packet %s for device %s: %s",
                    msg["title"],
                    msg["from"],
                    msg,
                )
                if "from" in msg and msg["from"] in self.devices:
                    await self.devices[msg["from"]].parse_message(msg)
                    if self.receive_callback:
                        await self.receive_callback()

    async def receive_messages(self) -> None:
        """Receive messages from the hub."""
        while True:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    msgdata = msg.json()
                    if type(msgdata) is list:
                        for part in msgdata:
                            await self.parse_message(part)
                    else:
                        await self.parse_message(msgdata)

    async def update(self) -> None:
        """Update the device states."""
        if not self.ws:
            await self.connect()
        await self.request_usrdta("ALL")
        for device in self.devices.values():
            await device.update()
