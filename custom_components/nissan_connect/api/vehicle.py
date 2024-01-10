from typing import Callable
import logging

from pydantic import parse_obj_as
from requests import Session

from .const import CV_BASE_URL
from .auth import TokenAuth
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
	def __init__(
		self,
		auth: TokenAuth,
		vin: str,
		*,
		pin: str = '',
		base_url: str=CV_BASE_URL
	):
		self.base_url = base_url
		self.vin = vin
		self.pin = pin
		self.session = Session()
		self.session.auth = auth
		self.session.headers.update({
			'vin': self.vin,
		})

	def get_status(self, service: Service, request_id: str = '') -> JSON:
		r = self.session.get(f'{self.base_url}/{service.value}/{request_id}').json()
		_LOGGER.debug(f'Service "{service.name}" response: {r}')
		return r

	def send_command(self, command: RemoteCommand) -> RequestStatusTracker:
		data = {'command': str(command)}
		if self.pin:
			data['pin'] = self.pin

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

	def door_lock(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.LOCK)

	def door_unlock(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.UNLOCK)

	def engine_start(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.START)

	def engine_stop(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.STOP)

	def engine_double_start(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.DOUBLE_START)

	def horn(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.HORN_ONLY)

	def lights(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.LIGHT_ONLY)

	def horn_and_lights(self) -> RequestStatusTracker:
		return self.send_command(RemoteCommand.HORN_LIGHT)
