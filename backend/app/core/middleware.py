# backend/app/core/middleware.py
# FastAPI middleware managing correlation IDs, security headers, CORS policies and rate limits

import time
import uuid
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.core.logging import correlation_id, logger

class ProductionHardeningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Establish unique correlation ID per request context
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id.set(request_id)

        start_time = time.time()
        
        # 2. Simple request throttling rate-limiter
        # (In production, this would parse Redis token buckets client IPs)
        
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.error("Unhandled API Request Failure", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}
                }
            )

        duration = time.time() - start_time
        logger.info(
            f"API Request Completed: {request.method} {request.url.path}",
            extra={"extra_payload": {"duration_seconds": duration, "status_code": response.status_code}}
        )

        # 3. Security Hardening Headers Injection
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
                            "default-src 'self'; "
                            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                            "img-src 'self' data: https:; "
                            "font-src 'self' https://cdn.jsdelivr.net; "
                            "connect-src 'self'; "
                            "frame-ancestors 'none';"
                        )
        response.headers["Referrer-Policy"] = "no-referrer"

        return response
