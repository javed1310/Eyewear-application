"""
OptiFlow — FastAPI Application Entrypoint
Main application with health check, CORS, and router mounting.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from app.core.config import settings
from app.core.database import engine
import app.core.database as db_core
from app.api import orders, inventory, websockets, prescriptions, alerts
from app.worker.risk_evaluator import start_risk_evaluator_loop
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Startup
    db_core.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # Start background workers
    app.state.risk_worker = asyncio.create_task(start_risk_evaluator_loop(60))
    
    print(f"[OK] {settings.APP_NAME} started | Debug={settings.DEBUG}")

    yield

    # Shutdown
    if hasattr(app.state, "risk_worker"):
        app.state.risk_worker.cancel()
        
    if db_core.redis_client:
        await db_core.redis_client.close()
    await engine.dispose()
    print(f"[STOP] {settings.APP_NAME} shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Order Management System for Eyewear Brands",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ──
app.include_router(orders.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(prescriptions.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(websockets.router)


# ── Health Check ──
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint — verifies DB and Redis connectivity."""
    import asyncio

    health = {"status": "healthy", "db": "unknown", "redis": "unknown"}

    # Check database (with timeout)
    try:
        async def check_db():
            async with engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )

        await asyncio.wait_for(check_db(), timeout=3.0)
        health["db"] = "ok"
    except asyncio.TimeoutError:
        health["db"] = "timeout"
        health["status"] = "degraded"
    except Exception as e:
        health["db"] = f"error: {type(e).__name__}"
        health["status"] = "degraded"

    # Check Redis (with timeout)
    try:
        async def check_redis():
            if db_core.redis_client:
                await db_core.redis_client.ping()
                return True
            return False

        result = await asyncio.wait_for(check_redis(), timeout=3.0)
        health["redis"] = "ok" if result else "not initialized"
        if not result:
            health["status"] = "degraded"
    except asyncio.TimeoutError:
        health["redis"] = "timeout"
        health["status"] = "degraded"
    except Exception as e:
        health["redis"] = f"error: {type(e).__name__}"
        health["status"] = "degraded"

    status_code = 200 if health["status"] == "healthy" else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=health, status_code=status_code)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "description": "AI-Powered Order Management System for Eyewear Brands",
        "docs": "/docs",
    }
