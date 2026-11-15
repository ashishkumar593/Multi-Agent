"""Application middleware for request correlation, timing, and security headers."""
import time
import uuid

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class RequestTracingMiddleware(BaseHTTPMiddleware):
        """Injects X-Request-ID and measures request latency."""

        async def dispatch(self, request: Request, call_next):
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            start_time = time.perf_counter()

            response: Response = await call_next(request)

            process_time = time.perf_counter() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Sec"] = f"{process_time:.4f}"
            return response
except ImportError:
    RequestTracingMiddleware = object  # type: ignore
