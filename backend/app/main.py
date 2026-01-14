from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import universe, repos, watchlist, admin
from app.config import settings

app = FastAPI(
    title="GitHub OSS Health API",
    description="Research-grade system for investor analysis of promising open-source projects",
    version="1.1.0",
)

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
