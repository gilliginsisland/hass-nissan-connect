class MissingTokenError(Exception):
	pass

class TokenRefreshError(Exception):
	pass

class TokenAuthError(TokenRefreshError):
	pass

class TokenApiError(TokenRefreshError):
	pass
