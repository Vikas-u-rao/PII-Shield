"""
PIIShield FastAPI Application Entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_proxy import router as proxy_router
from app.api.routes_admin import router as admin_router
from app.api.routes_analytics import router as analytics_router

app = FastAPI(
    title="PIIShield API",
    description="India-aware, Fail-Closed PII Protection Gateway for LLMs",
    version="0.1.0",
)

# CORS Middleware (configured for local frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "PIIShield API", "version": "0.1.0"}


# Router Registrations
app.include_router(proxy_router, prefix="/api/v1/proxy", tags=["Proxy Gateway"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics & Audit"])
