from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from . import models
from .database import engine
from .routes import router

# Create DB tables
try:
    print("Initializing database tables...")
    from . import models  # Explicitly import models to register them
    models.Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully (if they didn't exist).")
except Exception as e:
    print(f"Error initializing tables: {e}")

app = FastAPI(title="Prescription Extractor API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(router)

# Serve static files from frontend/web
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/web"))
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return RedirectResponse(url="/static/index.html")
