from dataclasses import dataclass
from time import time
from typing import Any, Protocol, Self

from .error import MissingTokenError


@dataclass
class Token():
	nna_refresh_token: str
	access_token: str
	id_token: str
	expires_at: int

	@classmethod
	def from_dict(cls, d: dict[str, Any]) -> Self:
		return cls(
			nna_refresh_token=str(d['nna_refresh_token']),
			access_token=str(d['access_token']),
			id_token=str(d['id_token']),
			expires_at=d.get('expires_at') or int(time()) + int(d['expires_in']),
		)

	def to_dict(self) -> dict[str, Any]:
		return {
			'nna_refresh_token': self.nna_refresh_token,
			'access_token': self.access_token,
			'id_token': self.id_token,
			'expires_at': self.expires_at,
		}


class TokenStorage(Protocol):
	def get(self) -> Token: ...
	def set(self, token: Token): ...


class SimpleTokenStorage():
	def __init__(self, token: Token | None = None) -> None:
		self._token = token

	def get(self) -> Token:
		if not self._token:
			raise MissingTokenError()
		return self._token

	def set(self, token: Token):
		self._token = token
