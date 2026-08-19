from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analyzers.pe_parser import UnsupportedFileError
from app.api.dependencies import get_detection_engine, get_yara_engine
from app.api.routes import analyses, dashboard, endpoints, settings as settings_route
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import init_db


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.resolved_storage_dir.mkdir(parents=True, exist_ok=True)
    settings.model_path.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    engine = get_detection_engine()
    yara_engine = get_yara_engine()
    model_status = "available" if engine.available else "unavailable"
    yara_status = "available" if yara_engine.available else "unavailable"
    logger.info(
        "application started",
        extra={"event": "startup", "status": model_status, "yara_status": yara_status},
    )
    yield
    logger.info("application stopped", extra={"event": "shutdown"})


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Static Windows PE classification and evidence reporting.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.exception_handler(UnsupportedFileError)
async def unsupported_file_handler(_request: Request, exc: UnsupportedFileError) -> JSONResponse:
    return JSONResponse(status_code=415, content={"detail": str(exc), "code": "unsupported_pe"})


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled API error", exc_info=exc, extra={"event": "api_error"})
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Check server logs for the event ID."},
    )


@app.get("/api/health", tags=["system"])
def health() -> dict[str, object]:
    engine = get_detection_engine()
    yara_engine = get_yara_engine()
    return {
        "status": "ok",
        "model_available": engine.available,
        "model_version": engine.model_version,
        "yara_available": yara_engine.available,
        "yara_ruleset_version": yara_engine.ruleset_version,
    }


app.include_router(analyses.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(endpoints.router, prefix="/api")
app.include_router(settings_route.router, prefix="/api")
