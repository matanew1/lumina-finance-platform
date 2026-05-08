from typing import Optional

from fastapi.responses import JSONResponse


def todo_response(message: str, *, endpoint: Optional[str] = None) -> JSONResponse:
    payload = {
        "status": "todo",
        "message": message,
        "endpoint": endpoint,
    }
    return JSONResponse(status_code=501, content=payload)
