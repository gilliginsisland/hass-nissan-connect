from time import time

from requests import Session
from requests.auth import AuthBase
from requests.models import PreparedRequest

from .const import TOKEN_URL
from .token import SimpleTokenStorage, Token, TokenStorage


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


class Auth(AuthBase):
	def __init__(
		self, *,
		token_url: str=TOKEN_URL,
		token_storage: TokenStorage | None = None,
	):
		self.cv_auth = CV('nissanus', 'cv.nissan.connect.us.android.25')
		self.session = Session()
		self.session.auth = self.cv_auth
		self.token_url = token_url
		self.token_storage = token_storage or SimpleTokenStorage()

	def _fetch(self, credentials: dict[str, str]):
		r = self.session.post(self.token_url, json=credentials)
		r.raise_for_status()
		self.token_storage.set(Token.from_dict(r.json()))

	def fetch_token(self, username: str, password: str):
		self._fetch({
			'email': username,
			'password': password,
		})

	def refresh_tokens(self):
		self._fetch({
			'refresh_token': self.token_storage.get().nna_refresh_token,
		})

	def __call__(self, r: PreparedRequest):
		token = self.token_storage.get()

		# refresh_tokens if the token will or has expired
		# in less than 10 minutes
		if token.expires_at - int(time()) < 600:
			self.refresh_tokens()

		r = self.cv_auth(r)
		r.headers.update({
			'Authorization': f'Bearer {token.access_token}',
			'id_token': token.id_token,
		})
		return r
