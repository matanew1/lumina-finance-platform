class AppError(Exception):
    status_code = 500
    detail = "Unexpected application error."

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        self.detail = detail or self.detail


class PersistenceError(AppError):
    detail = "Failed to persist changes."


class ValidationAppError(AppError):
    status_code = 400
    detail = "Invalid request."


class UnsupportedUploadFileError(ValidationAppError):
    detail = "Only .csv or .xlsx transaction files are supported."


class EmptyUploadFileError(ValidationAppError):
    detail = "Uploaded transaction file is empty."


class UploadParseError(ValidationAppError):
    detail = "Unable to parse uploaded transaction file."


class InsufficientQuantityError(ValidationAppError):
    detail = "Sell transaction exceeds available position."


class DuplicateTransactionError(AppError):
    status_code = 409
    detail = "One or more transactions have duplicate transaction IDs."
