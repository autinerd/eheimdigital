import websocket
from .EheimDigitalDevice import EheimDigitalDevice
from .EheimDigitalHub import EheimDigitalHub
from .const import SET_EHEATER_PARAM

class EheimDigitalHeater(EheimDigitalDevice):

	def __init__(self, hub: EheimDigitalHub, mac_address: str):
		super().__init__(hub, mac_address)

	def set_target_temp(self, target_temp: float):
		self.hub._send_payload({"from": "USER", 'to': self.mac_address, 'title': SET_EHEATER_PARAM, 'sollTemp': str(int(target_temp * 10))})

	def set_active(self, active: bool):
		self.hub._send_payload({"from": "USER", 'to': self.mac_address, 'title': SET_EHEATER_PARAM, 'active': 1 if active else 0})
