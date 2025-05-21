"""The Eheim Digital hub."""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING, Any, Callable

import aiohttp
from yarl import URL

from .autofeeder import EheimDigitalAutofeeder
from .classic_led_ctrl import EheimDigitalClassicLEDControl
from .classic_vario import EheimDigitalClassicVario
from .heater import EheimDigitalHeater
from .ph_control import EheimDigitalPHControl
from .types import (
    EheimDeviceType,
    EheimDigitalClientError,
    MeshNetworkPacket,
    MsgTitle,
    UsrDtaPacket,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from .device import EheimDigitalDevice


_LOGGER = getLogger(__package__)


class EheimDigitalHub:
    """Represent a Eheim Digital hub."""

    device_found_callback: Callable[[str, EheimDeviceType], Awaitable[None]] | None
    devices: dict[str, EheimDigitalDevice]
    loop: asyncio.AbstractEventLoop
    main: EheimDigitalDevice | None
    main_device_added_event: asyncio.Event | None = None
    receive_callback: Callable[[], Awaitable[None]] | None
    receive_task: asyncio.Task[None] | None = None
    session: aiohttp.ClientSession
    url: URL
    ws: aiohttp.ClientWebSocketResponse | None = None

    def __init__(
        self,
        *,
        host: str = "eheimdigital.local",
        session: aiohttp.ClientSession | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        receive_callback: Callable[[], Awaitable[None]] | None = None,
        main_device_added_event: asyncio.Event | None = None,
        device_found_callback: Callable[[str, EheimDeviceType], Awaitable[None]]
        | None = None,
    ) -> None:
        """Initialize a hub."""
        self.device_found_callback = device_found_callback
        self.devices = {}
        self.loop = loop or asyncio.get_event_loop()
        self.main = None
        self.main_device_added_event = main_device_added_event
        self.receive_callback = receive_callback
        self.session = session or aiohttp.ClientSession()
        self.url = URL.build(scheme="http", host=host, path="/ws")

    async def connect(self) -> None:  # pragma: no cover
        """Connect to the hub."""
        self.ws = await self.session.ws_connect(self.url)
        self.receive_task = self.loop.create_task(self.receive_messages())

    async def close(self) -> None:  # pragma: no cover
        """Close the connection."""
        if self.receive_task is not None:
            _ = self.receive_task.cancel()
        if self.ws is not None and not self.ws.closed:
            _ = await self.ws.close()

    async def add_device(self, usrdta: UsrDtaPacket) -> None:  # noqa: C901, PLR0912
        """Add a device to the device list."""
        match EheimDeviceType(usrdta["version"]):
            case EheimDeviceType.VERSION_EHEIM_EXT_HEATER:
                self.devices[usrdta["from"]] = EheimDigitalHeater(self, usrdta)
                if self.device_found_callback:
                    await self.device_found_callback(
                        usrdta["from"], EheimDeviceType(usrdta["version"])
                    )
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_VARIO:
                self.devices[usrdta["from"]] = EheimDigitalClassicVario(self, usrdta)
                if self.device_found_callback:
                    await self.device_found_callback(
                        usrdta["from"], EheimDeviceType(usrdta["version"])
                    )
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_LED_CTRL_PLUS_E:
                self.devices[usrdta["from"]] = EheimDigitalClassicLEDControl(
                    self, usrdta
                )
                if self.device_found_callback:
                    await self.device_found_callback(
                        usrdta["from"], EheimDeviceType(usrdta["version"])
                    )
            case EheimDeviceType.VERSION_EHEIM_PH_CONTROL:
                self.devices[usrdta["from"]] = EheimDigitalPHControl(self, usrdta)
                if self.device_found_callback:
                    await self.device_found_callback(
                        usrdta["from"], EheimDeviceType(usrdta["version"])
                    )
            case EheimDeviceType.VERSION_EHEIM_FEEDER:
                self.devices[usrdta["from"]] = EheimDigitalAutofeeder(self, usrdta)
                if self.device_found_callback:
                    await self.device_found_callback(
                        usrdta["from"], EheimDeviceType(usrdta["version"])
                    )
            case _:
                _LOGGER.debug(
                    "Found device %s with unsupported device type %s",
                    usrdta["from"],
                    EheimDeviceType(usrdta["version"]),
                )
        if self.main is None and usrdta["from"] in self.devices:
            self.main = self.devices[usrdta["from"]]
            if self.main_device_added_event:
                self.main_device_added_event.set()

    async def request_usrdta(self, mac_address: str) -> None:
        """Request the USRDTA of a device."""
        await self.send_packet({
            "title": MsgTitle.GET_USRDTA,
            "to": mac_address,
            "from": "USER",
        })

    async def send_packet(self, packet: dict[str, Any]) -> None:
        """Send a packet to the hub.

        Raises:
            EheimDigitalClientError: When there is an error with the connection.

        """
        if self.ws is not None:
            try:
                await self.ws.send_json(packet)
            except aiohttp.ClientError as err:
                raise EheimDigitalClientError from err

    async def parse_mesh_network(self, msg: MeshNetworkPacket) -> None:
        """Parse a MESH_NETWORK packet."""
        for client in msg["clientList"]:
            if client not in self.devices:
                await self.request_usrdta(client)

    async def parse_usrdta(self, msg: UsrDtaPacket) -> None:
        """Parse a USRDTA packet."""
        if msg["from"] not in self.devices:
            await self.add_device(msg)

    async def parse_message(self, msg: dict[str, Any]) -> None:
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
        if self.ws is None or self.ws.closed:
            _LOGGER.error("receive_task called without an established connection!")
            return
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    msgdata: list[dict[str, Any]] | dict[str, Any] = msg.json()
                    if isinstance(msgdata, list):
                        for part in msgdata:
                            await self.parse_message(part)
                    else:
                        await self.parse_message(msgdata)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.warning("Received error, reconnecting...:\n%s", msg.data)
                    await self.ws.close()
                    return
        except Exception:
            _LOGGER.exception(
                "Exception occurred on receiving messages",
                stack_info=True,
                stacklevel=5,
            )
            await self.ws.close()
            return

    async def update(self) -> None:
        """Update the device states."""
        if self.ws is None or self.ws.closed:
            _LOGGER.info("WebSocket connection to %s closed, reconnect...", self.url)
            await self.connect()
        await self.request_usrdta("ALL")
        for device in self.devices.values():
            await device.update()

    def as_dict(self) -> dict[str, Any]:
        """Return the hub as a dictionary."""
        return {
            "address": self.url.host,
            "mac_address": self.main.mac_address if self.main else None,
            "devices": {
                address: dev.as_dict() for address, dev in self.devices.items()
            },
        }
