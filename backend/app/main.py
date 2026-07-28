import os
import time
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application Startup
    logger.info("Initializing Prescription Extractor SaaS API...")
    auto_migrate()
    yield
    # Application Shutdown
    logger.info("Shutting down Prescription Extractor SaaS API...")

app = FastAPI(
    title="Prescription Extractor SaaS API",
    description="Enterprise-Grade Healthcare OCR & Prescription Data Extraction Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Global Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Universal CORS Middleware for Tandem Local & Vercel Deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost.*|http://127\.0\.0\.1.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "status_code": 500}
    )

# Include API Router
app.include_router(router)

# Serve Frontend Static Files
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/web"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/static/index.html")

# Production Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "unhealthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB ping failed: {e}")

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENV,
        "version": settings.VERSION
    }
