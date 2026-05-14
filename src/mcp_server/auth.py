from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Simple bearer-token auth for SSE mode."""

    def __init__(self, app, expected_api_key: str):
        super().__init__(app)
        self.expected_api_key = expected_api_key

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("authorization", "")
        expected = f"Bearer {self.expected_api_key}"
        if auth_header != expected:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)
