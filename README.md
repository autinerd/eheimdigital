# EHEIM.digital API wrapper in Python

This library is an API wrapper for the EHEIM.digital smart aquarium tools.


## Currently supported devices

- EHEIM autofeeder+
- EHEIM classicLEDcontrol+e
- EHEIM classicVARIO
- EHEIM thermocontrol
- EHEIM pHcontrol+e

## How to use

### Connect to a hub

```python
from aiohttp import ClientSession
from eheimdigital.hub import EheimDigitalHub

session = ClientSession(base_url="http://eheimdigital")
hub = EheimDigitalHub(session)
await hub.connect()
```
