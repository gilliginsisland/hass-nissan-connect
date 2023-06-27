from typing import List, Optional, Type
from enum import StrEnum
from datetime import datetime
from pydantic import BaseModel


class LockState(StrEnum):
	LOCKED = 'locked'
	UNLOCKED = 'unlocked'

class DoorState(StrEnum):
	OPEN = 'open'
	CLOSED = 'closed'

class RequestState(StrEnum):
	INITIATED = 'INITIATED'
	SUCCESS = 'SUCCESS'
	FAILED = 'FAILED'
	CANCELLATION_SUCCESS = 'CANCELLATION_SUCCESS'
	CANCELLATION_FAILED = 'CANCELLATION_FAILED'

class DoorCommand(StrEnum):
	LOCK = 'LOCK'
	UNLOCK = 'UNLOCK'

class EngineCommand(StrEnum):
	STOP = 'STOP'
	START = 'START'
	DOUBLE_START = 'DOUBLE_START'

class HornLightCommand(StrEnum):
	LIGHT_ONLY = 'LIGHT_ONLY'
	HORN_LIGHT = 'HORN_LIGHT'
	HORN_ONLY = 'HORN_ONLY'

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

class RequestStatus(BaseSchema):
	serviceRequestId: str
	serviceType: 'ServiceType'
	status: RequestState
	activationDateTime: Optional[datetime] = None
	statusChangeDateTime: Optional[datetime] = None
	command: Optional[str] = None

class LocationStatus(BaseSchema):
	status: Optional[str] = None
	serviceType: Optional[str] = None
	activationDateTime: Optional[datetime] = None
	statusChangeDateTime: Optional[datetime] = None
	location: GeoPoint

class Service(StrEnum):
	DOOR = 'DOOR', 'remote-door', DoorCommand, RequestStatus
	ENGINE = 'ENGINE', 'remote-engine', EngineCommand, RequestStatus
	HORN_AND_LIGHTS = 'HORN_AND_LIGHTS', 'remote-horn-and-lights', HornLightCommand, RequestStatus
	SERVICE_HISTORY = 'SERVICE_HISTORY', 'remote-service-history', None, List[RequestStatus]
	LOCATION = 'LOCATION', 'telemetry/location', None, LocationStatus
	VEHICLE_STATUS = 'VEHICLE_STATUS', 'telemetry/vehiclestatus', None, VehicleStatus

	def __new__(cls, *args):
		value = str(args[0])
		member = str.__new__(cls, value)
		member._value_ = value
		return member

	def __init__(self, _: str, path: str, command: Optional[Type[StrEnum]], schema: Type[BaseSchema]):
		self._path_ = path
		self._command_ = command
		self._schema_ = schema

	@property
	def path(self):
		return self._path_

	@property
	def command(self):
		return self._command_

	@property
	def schema(self):
		return self._schema_

class ServiceType(StrEnum):
	REMOTE_DOOR_LOCK = 'REMOTE_DOOR_LOCK', Service.DOOR
	REMOTE_DOOR_UNLOCK = 'REMOTE_DOOR_UNLOCK', Service.DOOR
	REMOTE_START = 'REMOTE_START', Service.ENGINE
	VEHICLE_LOCATOR = 'VEHICLE_LOCATOR', Service.LOCATION

	def __new__(cls, *args):
		value = str(args[0])
		member = str.__new__(cls, value)
		member._value_ = value
		return member

	def __init__(self, _: str, service: Service):
		self._service_ = service

	@property
	def service(self):
		return self._service_

# This is required because RequestStatus uses ServiceType
# and ServiceType just got defined
RequestStatus.update_forward_refs()
