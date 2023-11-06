from typing import Callable
import logging

from pydantic import parse_obj_as
from requests import Session

from .const import BASE_URL
from .auth import Auth
from .schema import (
	RemoteCommand,
	Service,
	RequestStatus,
	LocationStatus,
	VehicleStatus,
)

RequestStatusTracker = Callable[[], RequestStatus]
JSON = dict[str, 'JSON'] | list['JSON'] | int | str | float | bool | type[None]
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

	def get_status(self, service: Service, request_id: str = '') -> JSON:
		r = self.session.get(f'{self.base_url}/{service.value}/{request_id}').json()
		_LOGGER.debug(f'Service "{service.name}" response: {r}')
		return r

	def send_command(self, command: RemoteCommand, pin: str = '') -> RequestStatusTracker:
		data = {'command': str(command)}
		if pin:
			data['pin'] = pin

		r = self.session.post(f'{self.base_url}/{command.service.value}', json=data).json()
		_LOGGER.debug(f'Service "{command.service.name}::{command.name}" response: {r}')

		request_id = r['serviceRequestId']
		def status_tracker():
			return RequestStatus.parse_obj(
				self.get_status(command.service, request_id)
			)

		return status_tracker

	def vehicle_status(self) -> VehicleStatus:
		return VehicleStatus.parse_obj(
			self.get_status(Service.VEHICLE_STATUS)
		)

	def location(self) -> LocationStatus:
		return LocationStatus.parse_obj(
			self.get_status(Service.LOCATION)
		)

	def service_history(self) -> list[RequestStatus]:
		return parse_obj_as(
			list[RequestStatus],
			self.get_status(Service.SERVICE_HISTORY)
		)

	def door_lock(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.LOCK, pin)

	def door_unlock(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.UNLOCK, pin)

	def engine_start(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.START, pin)

	def engine_stop(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.STOP, pin)

	def engine_double_start(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.DOUBLE_START, pin)

	def horn(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.HORN_ONLY, pin)

	def lights(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.LIGHT_ONLY, pin)

	def horn_and_lights(self, pin: str = '') -> Callable[[], RequestStatus]:
		return self.send_command(RemoteCommand.HORN_LIGHT, pin)
