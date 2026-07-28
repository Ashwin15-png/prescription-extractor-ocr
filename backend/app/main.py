from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from . import models
from .database import engine, auto_migrate
from .routes import router
from .config import settings
from .logger import logger

# Initialize database schema automatically
try:
    logger.info("Initializing database schema...")
    models.Base.metadata.create_all(bind=engine)
    auto_migrate()
    logger.info("Database tables and columns verified successfully.")
except Exception as e:
    logger.error(f"Error initializing database tables: {e}")


app = FastAPI(
    title="Prescription Extractor API - AI Medical OCR",
    description="Production-Grade Healthcare SaaS API for Prescription OCR and Medical Data Extraction",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Input validation failed", "details": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected server error occurred."}
    )

# Register Router
app.include_router(router)

# Serve Frontend Web Static Files
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/web"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", tags=["System"])
async def read_index():
    return RedirectResponse(url="/static/index.html")

