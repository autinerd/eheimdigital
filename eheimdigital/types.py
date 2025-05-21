"""Types for Eheim Digital."""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Literal, NotRequired, TypedDict


class HeaterUnit(IntEnum):
    """Heater temperature unit."""

    CELSIUS = 0
    FAHRENHEIT = 1


class HeaterMode(IntEnum):
    """Heater operation mode."""

    MANUAL = 0
    SMART = 1
    BIO = 2


class FilterMode(IntEnum):
    """Filter operation mode."""

    MANUAL = 16
    PULSE = 8
    BIO = 4


class FilterErrorCode(IntEnum):
    """Filter error code."""

    NO_ERROR = 0
    ROTOR_STUCK = 1
    AIR_IN_FILTER = 2


class LightMode(StrEnum):
    """Light operation mode."""

    DAYCL_MODE = "DAYCL_MODE"
    MAN_MODE = "MAN_MODE"


class PHControlMode(IntEnum):
    """pHcontrol operation mode."""

    MANUAL_MODE = 0
    DAYCL_MODE = 1


class PHControlErrorCode(IntEnum):
    """pHcontrol error code."""

    NO_ERROR = 0
    PH_TOO_HIGH = 1
    PH_TOO_LOW = 2
    ELECTRODE_MISSING = 3


class FeederDrumState(IntEnum):
    """Feeder drum state."""

    GREEN = 0
    YELLOW = 1
    RED = 2
    MEASURING = 5


class MsgTitle(StrEnum):
    """Represent a message title."""

    USRDTA = "USRDTA"
    CLOCK = "CLOCK"
    NET_ST = "NET_ST"
    NET_AP = "NET_AP"
    MESH_NETWORK = "MESH_NETWORK"
    CLASSIC_VARIO_DATA = "CLASSIC_VARIO_DATA"
    HEATER_DATA = "HEATER_DATA"
    SET_EHEATER_PARAM = "SET_EHEATER_PARAM"
    GET_USRDTA = "GET_USRDTA"
    GET_EHEATER_DATA = "GET_EHEATER_DATA"
    GET_CLASSIC_VARIO_DATA = "GET_CLASSIC_VARIO_DATA"
    CCV = "CCV"
    MOON = "MOON"
    CLOUD = "CLOUD"
    ACCLIMATE = "ACCLIMATE"
    REQ_KEEP_ALIVE = "REQ_KEEP_ALIVE"
    PH_DATA = "PH_DATA"
    GET_PH_DATA = "GET_PH_DATA"
    FEEDER_DATA = "FEEDER_DATA"
    GET_FEEDER_DATA = "GET_FEEDER_DATA"
    SET_FEEDER_DATA = "SET_FEEDER_DATA"
    SET_FEEDER_TARA = "SET_FEEDER_TARA"
    SET_FEEDER_FULL = "SET_FEEDER_FULL"
    SET_MANUAL_FEED = "SET_MANUAL_FEED"
    SET_MANUAL_MEASUREMENT = "SET_MANUAL_MEASUREMENT"
    SET_STOP_FEEDER_SYNC = "SET_STOP_FEEDER_SYNC"


class EheimDeviceType(IntEnum):
    """Represent a device type."""

    VERSION_UNDEFINED = 0
    VERSION_HC = 1
    VERSION_HC_PLUS = 2
    VERSION_EHEIM_LIGHT = 3
    VERSION_EHEIM_EXT_FILTER = 4
    VERSION_EHEIM_EXT_HEATER = 5
    VERSION_EHEIM_FEEDER = 6
    VERSION_EHEIM_CHILLER = 7
    VERSION_EHEIM_LIGHT_AQUAKIDS = 8
    VERSION_EHEIM_PH_CONTROL = 9
    VERSION_EHEIM_STREAM_CONTROL = 10
    VERSION_EHEIM_REEFLEX = 11
    VERSION_EHEIM_80_FILTER_WITH_HEAT = 12
    VERSION_EHEIM_80_FILTER_WITHOUT_HEAT = 13
    VERSION_EHEIM_DOSING_PUMP = 14
    VERSION_EHEIM_LED_CTRL_PLUS_E = 15
    VERSION_EHEIM_RGB_CTRL_PLUS_E = 16
    VERSION_EHEIM_CLASSIC_LED_CTRL_PLUS_E = 17
    VERSION_EHEIM_CLASSIC_VARIO = 18
    VERSION_EHEIM_CONDUCTION_METER = 19
    VERSION_EHEIM_COMPACT_ON = 20

    @property
    def model_name(self) -> str | None:
        """Return the model name."""
        match self:
            case EheimDeviceType.VERSION_EHEIM_EXT_HEATER:
                return "thermocontrol+e"
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_VARIO:
                return "classicVARIO+e"
            case EheimDeviceType.VERSION_EHEIM_CLASSIC_LED_CTRL_PLUS_E:
                return "classicLEDcontrol+e"
            case EheimDeviceType.VERSION_EHEIM_PH_CONTROL:
                return "pHcontrol+e"
            case _:
                return None


MeshNetworkPacket = TypedDict(
    "MeshNetworkPacket",
    {"title": str, "to": str, "clientList": list[str], "from": NotRequired[str]},
)


UsrDtaPacket = TypedDict(
    "UsrDtaPacket",
    {
        "aqName": str,
        "build": NotRequired[list[str]],
        "demoUse": int,
        "dst": int,
        "emailAddr": str,
        "firmwareAvailable": int,
        "firstStart": int,
        "from": str,
        "fstTime": NotRequired[int],
        "groupID": int,
        "host": str,
        "language": str,
        "latestAvailableRevision": list[int],
        "liveTime": int,
        "meshing": int,
        "mode": NotRequired[str],
        "name": str,
        "netmode": str,
        "power": str,
        "remote": int,
        "revision": list[int],
        "softChange": NotRequired[int],
        "sstTime": NotRequired[int],
        "stMail": NotRequired[int],
        "stMailMode": NotRequired[int],
        "sysLED": int,
        "tankconfig": str,
        "tID": int,
        "timezone": int,
        "title": str,
        "to": str,
        "unit": int,
        "usrName": str,
        "version": int,
    },
)

HeaterDataPacket = TypedDict(
    "HeaterDataPacket",
    {
        "title": str,
        "from": str,
        "mUnit": int,
        "sollTemp": int,
        "isTemp": int,
        "hystLow": int,
        "hystHigh": int,
        "offset": int,
        "active": int,
        "isHeating": int,
        "mode": int,
        "sync": str,
        "partnerName": str,
        "dayStartT": int,
        "nightStartT": int,
        "nReduce": int,
        "alertState": int,
        "to": str,
    },
)

SetEheaterParamPacket = TypedDict(
    "SetEheaterParamPacket",
    {
        "title": Literal[MsgTitle.SET_EHEATER_PARAM],
        "to": str,
        "mUnit": int,
        "sollTemp": int,
        "active": int,
        "hystLow": int,
        "hystHigh": int,
        "offset": int,
        "mode": int,
        "sync": str,
        "partnerName": str,
        "dayStartT": int,
        "nightStartT": int,
        "nReduce": int,
        "from": Literal["USER"],
    },
)


ClassicVarioDataPacket = TypedDict(
    "ClassicVarioDataPacket",
    {
        "title": Literal[MsgTitle.CLASSIC_VARIO_DATA],
        "from": str,
        "rel_speed": int,
        "pumpMode": int,
        "filterActive": int,
        "turnOffTime": int,
        "serviceHour": int,
        "rel_manual_motor_speed": int,
        "rel_motor_speed_day": int,
        "rel_motor_speed_night": int,
        "startTime_day": int,
        "startTime_night": int,
        "pulse_motorSpeed_High": int,
        "pulse_motorSpeed_Low": int,
        "pulse_Time_High": int,
        "pulse_Time_Low": int,
        "turnTimeFeeding": int,
        "errorCode": int,
        "version": int,
    },
)

CCVPacket = TypedDict(
    "CCVPacket",
    {
        "title": Literal[MsgTitle.CCV],
        "from": str,
        "currentValues": list[int],
        "to": str,
    },
)

MoonPacket = TypedDict(
    "MoonPacket",
    {
        "title": Literal[MsgTitle.MOON],
        "from": str,
        "maxmoonlight": int,
        "minmoonlight": int,
        "moonlightActive": int,
        "moonlightCycle": int,
        "to": str,
    },
)

CloudPacket = TypedDict(
    "CloudPacket",
    {
        "title": Literal[MsgTitle.CLOUD],
        "from": str,
        "probability": int,
        "maxAmount": int,
        "minIntensity": int,
        "maxIntensity": int,
        "minDuration": int,
        "maxDuration": int,
        "cloudActive": int,
        "mode": int,
        "to": str,
    },
)

AcclimatePacket = TypedDict(
    "AcclimatePacket",
    {
        "title": Literal[MsgTitle.ACCLIMATE],
        "from": str,
        "duration": int,
        "intensityReduction": int,
        "currentAcclDay": int,
        "acclActive": int,
        "pause": int,
        "to": str,
    },
)

ClockPacket = TypedDict(
    "ClockPacket",
    {
        "title": Literal[MsgTitle.CLOCK],
        "from": str,
        "year": int,
        "month": int,
        "day": int,
        "hour": int,
        "min": int,
        "sec": int,
        "mode": NotRequired[str],
        "valid": NotRequired[int],
    },
)

PHDataPacket = TypedDict(
    "PHDataPacket",
    {
        "title": Literal[MsgTitle.PH_DATA],
        "from": str,
        "sollPH": int,
        "isPH": int,
        "active": int,
        "hystLow": int,
        "hystHigh": int,
        "offset": int,
        "valveIsActive": int,
        "acclimatization": int,
        "mode": int,
        "expert": int,
        "sync": str,
        "partnerName": str,
        "dayStartT": int,
        "nightStartT": int,
        "nReduce": int,
        "alertState": int,
        "serviceTime": int,
        "kH": int,
        "schedule": list[list[int]],
        "to": str,
    },
)

FeederDataPacket = TypedDict(
    "FeederDataPacket",
    {
        "title": Literal[MsgTitle.FEEDER_DATA],
        "from": str,
        "weight": float,
        "isSpinning": int,
        "level": list[int],
        "configuration": list[list[int]],
        "overfeeding": int,
        "sync": str,
        "partnerName": str,
        "sollRegulation": int,
        "feedingBreak": int,
        "breakDay": int,
        "turnTimeFeeding": int,
    },
)


class EheimDigitalClientError(Exception):
    """EHEIM Digital client error."""

    def __init__(self, *args: object) -> None:
        """Initialize exception."""
        super().__init__(*args)
