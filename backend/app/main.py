import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, properties, listings, deals, tours, analytics, favorites

app = FastAPI(
    title="Nadlan IL - Commercial Real Estate Marketplace",
    description="Israeli commercial real estate leasing and deal management platform",
    version="1.0.0",
)

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(deals.router, prefix="/api/deals", tags=["deals"])
app.include_router(tours.router, prefix="/api/tours", tags=["tours"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])


@app.get("/")
def root():
    return {
        "name": "Nadlan IL - Commercial Real Estate Marketplace",
        "name_he": "נדלן IL - מרקטפלייס נדל\"ן מסחרי",
        "version": "1.0.0",
        "docs": "/docs",
        "market": "Israel",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
