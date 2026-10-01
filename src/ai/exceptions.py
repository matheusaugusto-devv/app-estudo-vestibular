class AIException(Exception):
    pass


class AIAuthError(AIException):
    pass


class AIRateLimitError(AIException):
    pass


class AITimeoutError(AIException):
    pass


class AIResponseError(AIException):
    pass


class AIConnectionError(AIException):
    pass


class AINotConfiguredError(AIException):
    pass


class AIModelError(AIException):
    pass
