from typing import Optional, Tuple
import websocket
from .EheimDigitalHub import EheimDigitalHub

class EheimDigitalDevice:
	hub: EheimDigitalHub
	mac_address: str
	name: Optional[str]
	sw_version: Optional[str]

	def __init__(self, hub: EheimDigitalHub, mac_address: str):
		self.hub = hub
		self.mac_address = mac_address

	def get_device_details(self):
		data = self.hub.get_usrdta(self.mac_address)
		if data is not None:
			self.name = data["name"]
			version: list[int] = data["revision"]
			self.sw_version = f"{version[0]/1000}.{(version[0]%1000)/100}.{version[0]%100}_{version[1]/1000}.{(version[1]%1000)/100}.{version[1]%100}"
			print(self.name)
