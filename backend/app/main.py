from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.endpoints import universe, repos, watchlist, admin
from app.config import settings

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app = FastAPI(
    title="GitHub OSS Health API",
    description="Research-grade system for investor analysis of promising open-source projects",
    version="1.2.0",
)

# Attach rate limiter to app state and add exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://github-oss-health.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Allow POST for admin endpoints
    allow_headers=["*"],
)

# Include routers
app.include_router(universe.router, prefix="/api/universe", tags=["universe"])
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "GitHub OSS Health API",
        "version": "1.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
