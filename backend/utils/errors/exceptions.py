from collections.abc import Iterable

from sqlalchemy.exc import IntegrityError

UNIQUE_CONSTRAINT_MARKERS = (
    "duplicate key value violates unique constraint",
    "unique constraint failed",
    "duplicate entry",
)


class AppError(Exception):
    status_code = 500


class ConflictError(AppError):
    status_code = 409


class PersistenceError(AppError):
    status_code = 500


class NotFoundError(AppError):
    status_code = 404


class BadRequestError(AppError):
    status_code = 400


def is_unique_constraint_error(
    exc: IntegrityError,
    *,
    field_markers: Iterable[str] = (),
) -> bool:
    message = str(exc).lower()
    if not any(marker in message for marker in UNIQUE_CONSTRAINT_MARKERS):
        return False

    normalized_markers = tuple(marker.lower() for marker in field_markers)
    if not normalized_markers:
        return True

    return any(marker in message for marker in normalized_markers)
