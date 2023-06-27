from typing import Any, Callable, Optional, Self
from dataclasses import dataclass
from time import time

from requests import Session
from requests.auth import AuthBase
from requests.models import PreparedRequest

from .const import TOKEN_URL
from .error import MissingTokenError

class CV(AuthBase):
	def __init__(self, tenant_id: str, app_id: str) -> None:
		self.tenant_id = tenant_id
		self.app_id = app_id

	def __call__(self, r: PreparedRequest):
		r.headers.update({
			'CV-Tenant-Id': self.tenant_id,
			'CV-APPID': self.app_id,
		})
		return r

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

class Auth(AuthBase):
	def __init__(
		self, *,
		token_url: str=TOKEN_URL,
		token: Optional[Token]=None,
		token_updater: Optional[Callable[[Token], Any]]=None
	):
		self.cv_auth = CV('nissanus', 'cv.nissan.connect.us.android.25')
		self.session = Session()
		self.session.auth = self.cv_auth
		self.token_url = token_url
		self.token_updater = token_updater
		self._token = token

	@property
	def token(self) -> Token:
		if self._token is None:
			raise MissingTokenError()
		return self._token

	@token.setter
	def token(self, token: Token):
		if not isinstance(token, Token):
			raise ValueError(f'Token must be an instance of Token.')
		self._token = token
		if self.token_updater:
			self.token_updater(token)

	def fetch_tokens(self, username: str, password: str):
		r = self.session.post(self.token_url, json={
			'email': username,
			'password': password,
		})
		r.raise_for_status()
		self.token = Token.from_dict(r.json())

	def refresh_tokens(self):
		r = self.session.post(self.token_url, json={
			'refresh_token': self.token.nna_refresh_token,
		})
		r.raise_for_status()
		self.token = Token.from_dict(r.json())

	def __call__(self, r: PreparedRequest):
		# refresh_tokens if the token will or has expired
		# in less than 10 minutes
		if self.token.expires_at - int(time()) < 600:
			self.refresh_tokens()

		r = self.cv_auth(r)
		r.headers.update({
			'Authorization': f'Bearer {self.token.access_token}',
			'id_token': self.token.id_token,
		})
		return r
