class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="not_found", message=message, status_code=404)


class ProviderError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="upstream_error", message=message, status_code=502)
