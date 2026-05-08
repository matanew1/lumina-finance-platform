class AppError(Exception):
    status_code = 500


class ConflictError(AppError):
    status_code = 409


class PersistenceError(AppError):
    status_code = 500
