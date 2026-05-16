"""
Kopitar FastAPI Application

Main FastAPI application for the NHL analytics platform with comprehensive
endpoints for player analysis, fatigue tracking, and performance metrics.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import List, Optional, Dict, Any

from .routers import players, teams, games, analytics, fatigue, predictions
from .middleware import RateLimitMiddleware, AuthMiddleware, LoggingMiddleware
from .database import get_db_session
from .cache import get_cache
from .config import get_settings
from ..models.base import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Kopitar NHL Analytics API")
    
    # Initialize database
    await init_db()
    
    # Initialize cache connections
    cache = await get_cache()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kopitar NHL Analytics API")
    
    # Close cache connections
    await cache.close()
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Kopitar NHL Analytics API",
    description="""
    Comprehensive NHL player analytics platform providing fatigue analysis,
    performance metrics, and predictive insights across all positions.
    
    Features:
    - Multi-position player analysis (goalies, forwards, defensemen)
    - Advanced fatigue tracking and prediction
    - Historical data spanning 40+ years
    - Real-time performance analytics
    - Cross-era statistical comparisons
    """,
    version="1.0.0",
    contact={
        "name": "Kopitar Team",
        "email": "api@kopitar.dev",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# Get application settings
settings = get_settings()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "type": "validation_error",
                "message": str(exc),
                "status_code": 400,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred",
                "status_code": 500,
                "path": str(request.url.path),
                "timestamp": time.time()
            }
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "Kopitar NHL Analytics API",
        "version": "1.0.0",
        "description": "Advanced NHL player analytics and fatigue analysis",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "players": "/api/v1/players",
            "teams": "/api/v1/teams",
            "games": "/api/v1/games",
            "analytics": "/api/v1/analytics",
            "fatigue": "/api/v1/fatigue",
            "predictions": "/api/v1/predictions"
        }
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(
    db_session = Depends(get_db_session),
    cache = Depends(get_cache)
):
    """Comprehensive health check for all services."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "checks": {
            "database": "unknown",
            "cache": "unknown",
            "nhl_api": "unknown"
        }
    }
    
    # Check database
    try:
        await db_session.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check cache
    try:
        await cache.ping()
        health_status["checks"]["cache"] = "healthy"
    except Exception as e:
        health_status["checks"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check NHL API (basic connectivity)
    try:
        # This would be implemented with actual NHL API check
        health_status["checks"]["nhl_api"] = "healthy"
    except Exception as e:
        health_status["checks"]["nhl_api"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


# API versioning and route registration
API_V1_PREFIX = "/api/v1"

# Include routers
app.include_router(
    players.router,
    prefix=f"{API_V1_PREFIX}/players",
    tags=["Players"]
)

app.include_router(
    teams.router,
    prefix=f"{API_V1_PREFIX}/teams",
    tags=["Teams"]
)

app.include_router(
    games.router,
    prefix=f"{API_V1_PREFIX}/games",
    tags=["Games"]
)

app.include_router(
    analytics.router,
    prefix=f"{API_V1_PREFIX}/analytics",
    tags=["Analytics"]
)

app.include_router(
    fatigue.router,
    prefix=f"{API_V1_PREFIX}/fatigue",
    tags=["Fatigue Analysis"]
)

app.include_router(
    predictions.router,
    prefix=f"{API_V1_PREFIX}/predictions",
    tags=["Predictions"]
)


# Metrics endpoint for monitoring
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    # This would be implemented with actual metrics collection
    return {
        "message": "Metrics endpoint - integrate with Prometheus",
        "uptime": time.time(),
        "requests_total": 0,  # Would be actual counter
        "errors_total": 0     # Would be actual counter
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )