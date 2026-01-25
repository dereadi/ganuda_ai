"""
ganuda-api: Core API Patterns Library
Cherokee AI Federation - For the Seven Generations

CORE PACKAGE - Shared across all Assist applications

Features:
- Standard health check router
- Rate limiting middleware
- Request logging middleware
- Standard exception handlers
- CORS configuration helpers

Usage:
    from ganuda_api import health_router
    from ganuda_api.middleware import LoggingMiddleware, RateLimitMiddleware

    app = FastAPI()
    app.include_router(health_router)
    app.add_middleware(LoggingMiddleware)
"""

__version__ = "1.0.0"

# TODO: Extract from /ganuda/vetassist/backend/app/api/v1/endpoints/health.py
# TODO: Extract middleware patterns
