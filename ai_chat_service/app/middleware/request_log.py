import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            cost_ms = (time.perf_counter() - start_time) * 1000
            response.headers['X-Request-ID'] = request_id
            logger.info(
                "request_id=%s, method=%s, path=%s, status_code=%s, cost_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                cost_ms
            )
            return response
        except Exception:
            cost_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_id=%s, method=%s, path=%s, cost_ms=%.2f, error=unexpected",
                request_id,
                request.method,
                request.url.path,
                cost_ms,
            )
            raise
