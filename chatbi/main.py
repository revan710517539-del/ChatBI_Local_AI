from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from chatbi.config import ConfigModel, get_config

get_config().init_logger()  # noqa: F821

from chatbi import routers

# Import existing modules
from chatbi.database import PostgresDB, close_database, get_db, init_database
from chatbi.dependencies import PostgresSessionDep
from chatbi.middleware.error_handler import add_error_handlers
from chatbi.middleware.request import RequestLoggerMiddleware
from chatbi.middleware.standard_response import StandardResponseMiddleware

# init database data on startup
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         print("Initializing database data")
#         duckdb_init(True)
#         postgres_init()
#         print("Database data initialized")
#         yield
#     finally:
#         pass

app = FastAPI(
    title="SmartBI",
    description="A BI assistant powered by LLMs",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

origins = [
    "*",
    # "http://localhost",
    # "http://localhost:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: use lifespan to init database data
@app.on_event("startup")
async def startup_event():
    """Initialize resources during application startup."""
    logger.info("Starting ChatBI application")
    try:
        # Initialize database connections
        await init_database()
        logger.info("Database initialized successfully")
        
        # Initialize default datasource
        from chatbi.domain.datasource.init_default import init_default_datasource
        await init_default_datasource()
        
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}")
        # Don't raise here - let the app start and handle failures gracefully
        # Individual endpoints will check connection health


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources during application shutdown."""
    logger.info("Shutting down ChatBI application")
    await close_database()
    logger.info("Database connections closed")


app.include_router(routers.api_router)

# Add middlewares (order matters: bottom middleware executes first)
app.add_middleware(RequestLoggerMiddleware)

# Note: Rate limiting is now applied per-endpoint via dependencies
# See chatbi.dependencies.check_rate_limit_dependency

# Register all error handlers
add_error_handlers(app)


# api document
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint for application status."""
    return {"status": "ok", "message": "SmartBI API is running"}


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Checks the status of the database and returns health information.
    """
    # Check database health
    db_health = get_db().check_health()

    if db_health["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail="Database connection failed")

    health_data = {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": db_health["server_time"],
        "database": {
            "status": db_health["status"],
            "version": db_health["version"],
            "response_time_ms": db_health["response_time_ms"],
        },
    }

    # Explicitly return a dict, not including the SQLAlchemy session
    return health_data


# GET /config
@app.get("/config")
async def config():
    config = get_config()
    return JSONResponse(content=config.to_json())


# PATCH /config
@app.patch("/config")
async def update_config(cfg: ConfigModel):
    config = get_config()

    # only support update diagnose
    if cfg.diagnose is not None:
        config.update(diagnose=cfg.diagnose)
    if cfg.debug is not None:
        config.debug = cfg.debug

    return JSONResponse(content=config.to_json())
