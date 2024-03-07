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

class ServiceType(StrEnum):
	REMOTE_DOOR_LOCK = 'REMOTE_DOOR_LOCK'
	REMOTE_DOOR_UNLOCK = 'REMOTE_DOOR_UNLOCK'
	REMOTE_START = 'REMOTE_START'
	REMOTE_ENGINE = 'REMOTE_ENGINE'
	VEHICLE_LOCATOR = 'VEHICLE_LOCATOR'
	REMOTE_HORNBLOW_LIGHTFLASH = 'REMOTE_HORNBLOW_LIGHTFLASH'
	PERSONAL_DATA_WIPE = 'PERSONAL_DATA_WIPE'
	VEHICLE_HEALTH_REPORT = 'VEHICLE_HEALTH_REPORT'
	POI = 'POI'
	RECALL_CAMPAIGN_ADVISOR = 'RECALL_CAMPAIGN_ADVISOR'
	PANIC_ALERT = 'PANIC_ALERT'
	AUTO_DTC_ALERT = 'AUTO_DTC_ALERT'
	MAINTAINENCE_ALERT = 'MAINTAINENCE_ALERT'
	STOLEN_VEHICLE_TRACKER = 'STOLEN_VEHICLE_TRACKER'
	GEOFENCE = 'GEOFENCE'
	VALET = 'VALET'
	SPEED = 'SPEED'
	CURFEW = 'CURFEW'
	DAILY_ROUTE_GUIDANCE = 'DAILY_ROUTE_GUIDANCE'
	ACN = 'ACN'
	SOS = 'SOS'
	ENHANCED_ROADSIDE_ASSISTANCE = 'ENHANCED_ROADSIDE_ASSISTANCE'
	VEHICLE_IMMOBILIZATION = 'VEHICLE_IMMOBILIZATION'
	ALARM_NOTIFICATION = 'ALARM_NOTIFICATION'
	ECO_COACH = 'ECO_COACH'
	POI_VIA_IVR = 'POI_VIA_IVR'
	SERVICE_LINK = 'SERVICE_LINK'
	WEATHER = 'WEATHER'
	TRAFFIC_FLOW = 'TRAFFIC_FLOW'
	TURN_BY_TURN_NAVIGATION = 'TURN_BY_TURN_NAVIGATION'
	RESTAURANT_RATING = 'RESTAURANT_RATING'
	GAS_PRICE_LOCATOR = 'GAS_PRICE_LOCATOR'
	LOCATION_SHARING = 'LOCATION_SHARING'

	@property
	def service(self) -> Service | None:
		return _service_type_service_map[self]

_service_type_service_map: dict[ServiceType,Service] = {
	ServiceType.REMOTE_DOOR_LOCK:  Service.DOOR,
	ServiceType.REMOTE_DOOR_UNLOCK:  Service.DOOR,
	ServiceType.REMOTE_START:  Service.ENGINE,
	ServiceType.REMOTE_ENGINE:  Service.ENGINE,
	ServiceType.VEHICLE_LOCATOR:  Service.LOCATION,
	ServiceType.REMOTE_HORNBLOW_LIGHTFLASH:  Service.HORN_AND_LIGHTS,
}

class RemoteCommand(StrEnum):
	LOCK = 'LOCK'
	UNLOCK = 'UNLOCK'
	STOP = 'STOP'
	REMOTE_STOP = 'STOP'
	START = 'START'
	REMOTE_START = 'START'
	DOUBLE_START = 'DOUBLE_START'
	LIGHT_ONLY = 'LIGHT_ONLY'
	HORN_LIGHT = 'HORN_LIGHT'
	HORN_ONLY = 'HORN_ONLY'

	@property
	def service(self) -> Service:
		return _remote_command_service_map[self]

_remote_command_service_map: dict[RemoteCommand,Service] = {
	RemoteCommand.LOCK: Service.DOOR,
	RemoteCommand.UNLOCK: Service.DOOR,
	RemoteCommand.STOP: Service.ENGINE,
	RemoteCommand.REMOTE_STOP: Service.ENGINE,
	RemoteCommand.START: Service.ENGINE,
	RemoteCommand.REMOTE_START: Service.ENGINE,
	RemoteCommand.DOUBLE_START: Service.ENGINE,
	RemoteCommand.LIGHT_ONLY: Service.HORN_AND_LIGHTS,
	RemoteCommand.HORN_LIGHT: Service.HORN_AND_LIGHTS,
	RemoteCommand.HORN_ONLY: Service.HORN_AND_LIGHTS,
}


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
	status: str | None = None
	serviceType: str | None = None
	activationDateTime: datetime | None = None
	statusChangeDateTime: datetime | None = None
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
	activationDateTime: datetime | None = None
	statusChangeDateTime: datetime | None = None
	command: RemoteCommand | None = None
