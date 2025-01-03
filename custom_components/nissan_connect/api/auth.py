from time import time

from requests import (
	Session,
	PreparedRequest,
	HTTPError,
)
from requests.auth import AuthBase

from .const import (
	NISSAN_CONNECT_APP_ID,
	NISSAN_TENANT_ID,
	NISSAN_TOKEN_URL,
)
from .error import (
	TokenApiError,
	TokenAuthError,
	TokenRefreshError,
)
from .token import (
	Token,
	TokenStorage,
	SimpleTokenStorage,
)


class CVAuth(AuthBase):
	def __init__(self, tenant_id: str, app_id: str) -> None:
		self.tenant_id = tenant_id
		self.app_id = app_id

	def __call__(self, r: PreparedRequest):
		r.headers.update({
			'CV-Tenant-Id': self.tenant_id,
			'CV-APPID': self.app_id,
		})
		return r


class TokenAuth(AuthBase):
	def __init__(
		self, *,
		tenant_id: str=NISSAN_TENANT_ID,
		app_id: str=NISSAN_CONNECT_APP_ID,
		token_url: str=NISSAN_TOKEN_URL,
		token_storage: TokenStorage | None = None,
	):
		self._cv_auth = CVAuth(tenant_id, app_id)
		self._session = Session()
		self._session.auth = self._cv_auth
		self._token_url = token_url
		self._token_storage = token_storage or SimpleTokenStorage()

	@property
	def token(self) -> Token:
		return self._token_storage.get()

	@token.setter
	def token(self, token: Token):
		self._token_storage.set(token)

	def _post(self, credentials: dict[str, str]):
		try:
			r = self._session.post(self._token_url, json=credentials)
			r.raise_for_status()
		except HTTPError as err:
			if 400 <= err.response.status_code < 500:
				raise TokenAuthError(err) from err
			else:
				raise TokenApiError(err) from err
		except Exception as err:
			raise TokenRefreshError(err) from err

		self._token_storage.set(Token.from_dict(r.json()))

	def generate(self, username: str, password: str):
		self._post({
			'email': username,
			'password': password,
		})

	def refresh(self):
		self._post({
			'refresh_token': self._token_storage.get().nna_refresh_token,
		})

	def __call__(self, r: PreparedRequest):
		token = self._token_storage.get()

		# refresh_tokens if the token will or has expired
		# in less than 10 minutes
		if token.expires_at - int(time()) < 600:
			self.refresh()

		r = self._cv_auth(r)
		r.headers.update({
			'Authorization': f'Bearer {token.access_token}',
			'id_token': token.id_token,
		})
		return r
