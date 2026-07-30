import os
import time
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text

from .config import settings
from .database import engine, auto_migrate, get_db
from .routes import router
from .logger import logger

# ── Startup / Shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Prescription Extractor SaaS API...")
    auto_migrate()
    logger.info("API ready.")
    yield
    logger.info("Shutting down Prescription Extractor SaaS API...")


# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Prescription Extractor SaaS API",
    description="Enterprise-Grade Healthcare OCR & Prescription Data Extraction Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS (allow all for dev; also allows *.vercel.app) ───────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost.*|http://127\.0\.0\.1.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Process-Time"],
)

# ── Security + Timing Middleware ──────────────────────────────────────────────
@app.middleware("http")
async def add_security_and_timing_headers(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Last-resort safety net — should normally be caught at handler level
        logger.error(f"Unhandled middleware exception: {exc}\n{traceback.format_exc()}")
        response = JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error.", "details": str(exc)},
        )
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"]       = f"{elapsed:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]       = "DENY"
    response.headers["X-XSS-Protection"]      = "1; mode=block"
    if elapsed > 5:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {elapsed:.2f}s")
    return response

# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return JSON — never HTML — for HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail, "status_code": exc.status_code},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all so the frontend always gets JSON, never a raw traceback page."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An internal server error occurred.",
            "details": str(exc),
        },
    )

# ── Router ────────────────────────────────────────────────────────────────────
app.include_router(router)

# ── Static frontend ───────────────────────────────────────────────────────────
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/web")
)
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/static/index.html")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "unhealthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error(f"Health check DB ping failed: {exc}")

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENV,
        "version": settings.VERSION,
    }
