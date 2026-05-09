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
    '''
    Checks if the provided filename has an allowed extension.
    - Parameters:
        - filename: str | None - The name of the file to check.
        - allowed_extensions: tuple[str, ...] - A tuple of allowed file extensions (e.g., (".csv", ".xlsx")).
    - Returns:
        - bool: True if the filename has an allowed extension, False otherwise.
    '''
    return bool(filename) and Path(filename).suffix.lower() in allowed_extensions


async def read_table_from_file(file: UploadFile, allowed_extensions: tuple[str, ...] = (".csv", ".xlsx")) -> pd.DataFrame:
    '''
    Reads a table from a file and loads it into a pandas DataFrame.
    - Parameters:
        - file: UploadFile - The file containing the table data.
        - allowed_extensions: tuple[str, ...] - A tuple of allowed file extensions.
    - Returns:
        - pd.DataFrame: The DataFrame containing the table data.
    '''

    # Check if the file has an allowed extension (CSV or Excel)
    if not has_allowed_extension(file.filename, allowed_extensions):
        raise UnsupportedUploadFileError() # The file extension is not supported for transaction uploads.

    # Read the contents of the uploaded file
    contents = await file.read()

    # If the file is empty, raise an error indicating that the uploaded file contains no data.
    if not contents:    
        raise EmptyUploadFileError(f"Uploaded file {file.filename} contains no data.")

    try:
        # Attempt to read the file into a DataFrame based on its extension. If the extension is .csv, use pd.read_csv; if it's .xlsx, use pd.read_excel.
        if Path(file.filename or "").suffix.lower() == ".csv":
            # Read the CSV file into a DataFrame, treating all data as strings to avoid type inference issues.
            dataframe = pd.read_csv(BytesIO(contents), dtype=str)
        else:
            # Read the Excel file into a DataFrame using the openpyxl engine, treating all data as strings to avoid type inference issues.
            dataframe = pd.read_excel(BytesIO(contents), engine="openpyxl", dtype=str)
    except Exception as exc:
        raise UploadParseError() from exc

    # If the resulting DataFrame is empty, raise an error indicating that the uploaded file contains no data.
    if dataframe.empty:
        raise EmptyUploadFileError(f"Uploaded file {file.filename} contains no data.")

    # Return the loaded DataFrame
    return dataframe
