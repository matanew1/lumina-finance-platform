from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from backend.app.utils.exceptions import (
    EmptyUploadFileError,
    UnsupportedUploadFileError,
    UploadParseError,
)


def has_allowed_extension(
    filename: str | None,
    allowed_extensions: tuple[str, ...],
) -> bool:
    return bool(filename) and Path(filename).suffix.lower() in allowed_extensions


async def read_transaction_file(file: UploadFile) -> pd.DataFrame:
    if not has_allowed_extension(file.filename, (".csv", ".xlsx")):
        raise UnsupportedUploadFileError()

    contents = await file.read()
    if not contents:
        raise EmptyUploadFileError()

    try:
        if Path(file.filename or "").suffix.lower() == ".csv":
            dataframe = pd.read_csv(BytesIO(contents), dtype=str)
        else:
            dataframe = pd.read_excel(BytesIO(contents), engine="openpyxl", dtype=str)
    except Exception as exc:
        raise UploadParseError() from exc

    if dataframe.empty:
        raise EmptyUploadFileError(
            "Uploaded transaction file contains no transaction rows."
        )

    return dataframe
