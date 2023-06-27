from typing import (
	Literal,
	Sequence,
	overload,
	Type
)
from enum import StrEnum
import logging

from pydantic import parse_obj_as
from requests import Session

from .const import BASE_URL
from .auth import Auth
from .schema import (
	BaseSchema,
	Service,
	DoorCommand,
	EngineCommand,
	HornLightCommand,
	RequestStatus,
	LocationStatus,
	VehicleStatus,
)

JSON = dict[str, 'JSON'] | list['JSON'] | int | str | float | bool | Type[None]
_LOGGER = logging.getLogger(__name__)


class Vehicle():
	def __init__(self, auth: Auth, vin: str, *, base_url: str=BASE_URL):
		self.base_url = base_url
		self.vin = vin
		self.session = Session()
		self.session.auth = auth
		self.session.headers.update({
			'vin': self.vin,
		})

	@overload
	def get(self, service: Literal[Service.DOOR], request_id: str = '') -> RequestStatus:
		...
	@overload
	def get(self, service: Literal[Service.ENGINE], request_id: str = '') -> RequestStatus:
		...
	@overload
	def get(self, service: Literal[Service.HORN_AND_LIGHTS], request_id: str = '') -> RequestStatus:
		...
	@overload
	def get(self, service: Literal[Service.SERVICE_HISTORY]) -> list[RequestStatus]:
		...
	@overload
	def get(self, service: Literal[Service.VEHICLE_STATUS]) -> VehicleStatus:
		...
	@overload
	def get(self, service: Literal[Service.LOCATION]) -> LocationStatus:
		...
	@overload
	def get(self, service: Service) -> BaseSchema | Sequence[BaseSchema]:
		...
	@overload
	def get(self, service: Service, request_id: str = '') -> RequestStatus:
		...
	def get(self, service: Service, request_id: str = '') -> BaseSchema | Sequence[BaseSchema]:
		r = self.session.get(f'{self.base_url}/{service.path}/{request_id}').json()
		_LOGGER.debug(f'Service "{service.name}" response: {r}')
		return parse_obj_as(service.schema, r)

	@overload
	def post(self, service: Literal[Service.DOOR], command: DoorCommand, pin: str = '') -> str:
		...
	@overload
	def post(self, service: Literal[Service.ENGINE], command: EngineCommand, pin: str = '') -> str:
		...
	@overload
	def post(self, service: Literal[Service.HORN_AND_LIGHTS], command: HornLightCommand, pin: str = '') -> str:
		...
	@overload
	def post(self, service: Service, command: StrEnum, pin: str = '') -> str:
		...
	def post(self, service: Service, command: StrEnum, pin: str = '') -> str:
		data = {'command': command.value}
		if pin:
			data['pin'] = pin
		r = self.session.post(f'{self.base_url}/{service.path}', json=data).json()
		_LOGGER.debug(f'Service "{service.name}" response: {r}')
		return r['serviceRequestId']

	def vehicle_status(self) -> VehicleStatus:
		return self.get(Service.VEHICLE_STATUS)

	def location(self) -> LocationStatus:
		return self.get(Service.LOCATION)

	def service_history(self) -> list[RequestStatus]:
		return self.get(Service.SERVICE_HISTORY)

	def door_lock(self, pin: str = '') -> str:
		return self.post(Service.DOOR, DoorCommand.LOCK, pin)

	def door_unlock(self, pin: str = '') -> str:
		return self.post(Service.DOOR, DoorCommand.UNLOCK, pin)

	def door_history(self, request_id: str = '') -> RequestStatus:
		return self.get(Service.DOOR, request_id)

	def engine_start(self, pin: str = '') -> str:
		return self.post(Service.ENGINE, EngineCommand.START, pin)

	def engine_stop(self, pin: str = '') -> str:
		return self.post(Service.ENGINE, EngineCommand.STOP, pin)

	def engine_double_start(self, pin: str = '') -> str:
		return self.post(Service.ENGINE, EngineCommand.DOUBLE_START, pin)

	def engine_history(self, request_id: str = '') -> RequestStatus:
		return self.get(Service.ENGINE, request_id)

	def horn(self, pin: str = '') -> str:
		return self.post(Service.HORN_AND_LIGHTS, HornLightCommand.HORN_ONLY, pin)

	def lights(self, pin: str = '') -> str:
		return self.post(Service.HORN_AND_LIGHTS, HornLightCommand.LIGHT_ONLY, pin)

	def horn_and_lights(self, pin: str = '') -> str:
		return self.post(Service.HORN_AND_LIGHTS, HornLightCommand.HORN_LIGHT, pin)

	def horn_lights_history(self, request_id: str = '') -> RequestStatus:
		return self.get(Service.HORN_AND_LIGHTS, request_id)
