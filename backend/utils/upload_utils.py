from io import BytesIO

import pandas as pd
from fastapi import UploadFile


async def read_upload_bytes(
    file: UploadFile,
    *, # pylint: disable=unused-argument
    allowed_extensions: tuple[str, ...] | None = None,
    unsupported_message: str = "Unsupported file type.",
    empty_message: str = "Uploaded file is empty.",
) -> bytes:
    if allowed_extensions and not has_allowed_extension(file.filename, allowed_extensions):
        raise ValueError(unsupported_message)

    contents = await file.read()
    if not contents:
        raise ValueError(empty_message)

    return contents


async def read_excel_upload(
    file: UploadFile,
    *, # pylint: disable=unused-argument
    allowed_extensions: tuple[str, ...] = (".xlsx",),
    unsupported_message: str = "Only Excel files are supported.",
    empty_message: str = "Uploaded Excel file is empty.",
    parse_error_message: str = "Unable to parse uploaded Excel file.",
    empty_dataframe_message: str = "Uploaded Excel file contains no rows.",
) -> pd.DataFrame:
    contents = await read_upload_bytes(
        file,
        allowed_extensions=allowed_extensions,
        unsupported_message=unsupported_message,
        empty_message=empty_message,
    )

    try:
        dataframe = pd.read_excel(BytesIO(contents), engine="openpyxl")
    except Exception as exc:
        raise ValueError(parse_error_message) from exc

    if dataframe.empty:
        raise ValueError(empty_dataframe_message)

    return dataframe


def has_allowed_extension(filename: str | None, allowed_extensions: tuple[str, ...]) -> bool:
    if not filename:
        return False
    return filename.lower().endswith(tuple(extension.lower() for extension in allowed_extensions))
