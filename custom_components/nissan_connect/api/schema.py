from typing import Optional
from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel


class Service(StrEnum):
	DOOR = 'remote-door'
	ENGINE = 'remote-engine'
	HORN_AND_LIGHTS = 'remote-horn-and-lights'
	SERVICE_HISTORY = 'remote-service-history'
	LOCATION = 'telemetry/location'
	VEHICLE_STATUS = 'telemetry/vehiclestatus'

class _ServiceEnum(StrEnum):
	def __new__(cls, service, *_):
		value = str(service)
		member = str.__new__(cls, value)
		member._value_ = value
		return member

	def __init__(self, _: str, service: Service):
		self._service_ = service

	@property
	def service(self) -> Service:
		return self._service_

class ServiceType(_ServiceEnum):
	service_type = '', None
	REMOTE_DOOR_LOCK = 'REMOTE_DOOR_LOCK', Service.DOOR
	REMOTE_DOOR_UNLOCK = 'REMOTE_DOOR_UNLOCK', Service.DOOR
	REMOTE_START = 'REMOTE_START', Service.ENGINE
	REMOTE_ENGINE = 'REMOTE_ENGINE', Service.ENGINE
	VEHICLE_LOCATOR = 'VEHICLE_LOCATOR', Service.LOCATION
	REMOTE_HORNBLOW_LIGHTFLASH = 'REMOTE_HORNBLOW_LIGHTFLASH', Service.HORN_AND_LIGHTS
	PERSONAL_DATA_WIPE = 'PERSONAL_DATA_WIPE', None
	VEHICLE_HEALTH_REPORT = 'VEHICLE_HEALTH_REPORT', None
	POI = 'POI', None
	RECALL_CAMPAIGN_ADVISOR = 'RECALL_CAMPAIGN_ADVISOR', None
	PANIC_ALERT = 'PANIC_ALERT', None
	AUTO_DTC_ALERT = 'AUTO_DTC_ALERT', None
	MAINTAINENCE_ALERT = 'MAINTAINENCE_ALERT', None
	STOLEN_VEHICLE_TRACKER = 'STOLEN_VEHICLE_TRACKER', None
	GEOFENCE = 'GEOFENCE', None
	VALET = 'VALET', None
	SPEED = 'SPEED', None
	CURFEW = 'CURFEW', None
	DAILY_ROUTE_GUIDANCE = 'DAILY_ROUTE_GUIDANCE', None
	ACN = 'ACN', None
	SOS = 'SOS', None
	ENHANCED_ROADSIDE_ASSISTANCE = 'ENHANCED_ROADSIDE_ASSISTANCE', None
	VEHICLE_IMMOBILIZATION = 'VEHICLE_IMMOBILIZATION', None
	ALARM_NOTIFICATION = 'ALARM_NOTIFICATION', None
	ECO_COACH = 'ECO_COACH', None
	POI_VIA_IVR = 'POI_VIA_IVR', None
	SERVICE_LINK = 'SERVICE_LINK', None
	WEATHER = 'WEATHER', None
	TRAFFIC_FLOW = 'TRAFFIC_FLOW', None
	TURN_BY_TURN_NAVIGATION = 'TURN_BY_TURN_NAVIGATION', None
	RESTAURANT_RATING = 'RESTAURANT_RATING', None
	GAS_PRICE_LOCATOR = 'GAS_PRICE_LOCATOR', None
	LOCATION_SHARING = 'LOCATION_SHARING', None

class RemoteCommand(_ServiceEnum):
	LOCK = 'LOCK', Service.DOOR
	UNLOCK = 'UNLOCK', Service.DOOR
	STOP = 'STOP', Service.ENGINE
	REMOTE_STOP = STOP
	START = 'START', Service.ENGINE
	REMOTE_START = START
	DOUBLE_START = 'DOUBLE_START', Service.ENGINE
	LIGHT_ONLY = 'LIGHT_ONLY', Service.HORN_AND_LIGHTS
	HORN_LIGHT = 'HORN_LIGHT', Service.HORN_AND_LIGHTS
	HORN_ONLY = 'HORN_ONLY', Service.HORN_AND_LIGHTS


class BaseSchema(BaseModel):
	def __getitem__(self, item: str):
		return getattr(self, item)

class Counter(BaseSchema):
	unit: str
	value: int

class GeoPoint(BaseSchema):
	latitude: float
	longitude: float
	latlongUOM: str

class CockpitStatus(BaseSchema):
	fuelAutonomy: Counter
	totalMileage: Counter

class PressureStatus(BaseSchema):
	flPressure: Counter
	frPressure: Counter
	rlPressure: Counter
	rrPressure: Counter
	flStatus: bool
	frStatus: bool
	rlStatus: bool
	rrStatus: bool

class MalfunctionIndicatorLampsStatus(BaseSchema):
	absWarning: bool
	airbagWarning: bool
	brakeFluidWarning: bool
	oilPressureWarning: bool
	tyrePressureWarning: bool
	oilPressureSwitch: bool
	lampRequest: bool

class HealthStatus(BaseSchema):
	malfunctionIndicatorLamps: MalfunctionIndicatorLampsStatus

class LockState(StrEnum):
	LOCKED = 'locked'
	UNLOCKED = 'unlocked'

class DoorState(StrEnum):
	OPEN = 'open'
	CLOSED = 'closed'

class LockStatus(BaseSchema):
	lockStatus: LockState
	doorStatusFrontLeft: DoorState
	doorStatusFrontRight: DoorState
	doorStatusRearLeft: DoorState
	doorStatusRearRight: DoorState
	engineHoodStatus: DoorState
	hatchStatus: DoorState

class VehicleStatus(BaseSchema):
	lastUpdateTime: datetime
	cockpit: CockpitStatus
	pressure: PressureStatus
	healthStatus: HealthStatus
	lockStatus: LockStatus

class LocationStatus(BaseSchema):
	status: Optional[str] = None
	serviceType: Optional[str] = None
	activationDateTime: Optional[datetime] = None
	statusChangeDateTime: Optional[datetime] = None
	location: GeoPoint

class RequestState(StrEnum):
	INITIATED = 'INITIATED'
	SUCCESS = 'SUCCESS'
	FAILED = 'FAILED'
	CANCELLATION_SUCCESS = 'CANCELLATION_SUCCESS'
	CANCELLATION_FAILED = 'CANCELLATION_FAILED'

class RequestStatus(BaseSchema):
	serviceRequestId: str
	serviceType: ServiceType
	status: RequestState
	activationDateTime: Optional[datetime] = None
	statusChangeDateTime: Optional[datetime] = None
	command: Optional[RemoteCommand] = None
