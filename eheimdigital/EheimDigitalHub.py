from contextlib import closing
import select
import websocket
import json
import typing

class EheimDigitalHub():
	host: str = "eheimdigital"
	devices = []

	def __init__(self, host: str = 'eheimdigital'):
		self.host = host
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			data = json.loads(conn.recv_frame().data)

	async def discover_devices(self) -> list:
		devices = []
		data = []
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			while conn in select.select([conn], [], [], 1)[0]:
				data += json.loads(conn.recv())
				# json.dumps({"title": "SET_EHEATER_PARAM", "to": "44:17:93:26:00:A4", "sollTemp": 205, "from": "USER"})
			for obj in data:
				if 'title' in obj and obj['title'] == 'MESH_NETWORK':
					for mac_address in obj['clientList']:
						types = [obj for obj in data if 'from' in obj and obj['from'] == mac_address and 'title' in obj and obj['title'].endswith('_DATA')]
						if len(types) == 1:
							if types[0]['title'] == 'HEATER_DATA':
								from .EheimDigitalHeater import EheimDigitalHeater
								print(f'found heater: {mac_address}')
								devices.append(EheimDigitalHeater(self, mac_address))
		return devices

	def get_usrdta(self, to: str) -> typing.Optional[dict]:
		data = []
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			conn.send(json.dumps({"title":"GET_USRDTA","to":to,"from":"USER"}))
			while conn in select.select([conn], [], [], 1)[0]:
				a = json.loads(conn.recv())
				if type(a) == list:
					data += a
				elif type(a) == dict:
					data.append(a)
			for obj in data:
				if 'title' in obj and obj['title'] == 'USRDTA' and obj['from'] == to:
					return obj
			return None

	def fetch_data(self) -> list[dict]:
		data = []
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			while conn in select.select([conn], [], [], 1)[0]:
				a = json.loads(conn.recv())
				if type(a) == list:
					data += a
				elif type(a) == dict:
					data.append(a)
		return data

			
	def _send_payload(self, payload: dict):
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			conn.send(json.dumps(payload))

	def start_firmware_update(self):
		with closing(websocket.create_connection(f'ws://{self.host}/ws')) as conn:
			conn.send('{"title":"START_FOTA","to":"ALL","from":"USER"}')