import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import init_db
from .routers import rooms, bookings

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database schema at startup."""
    # SQLite dev path: creates tables automatically
    init_db()
    yield


app = FastAPI(
    title="Tourstay Portal API",
    description="Web-Based Hotel Reservation System for Tourists (SE2030)",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:8000"
)
allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under /api/v1
app.include_router(rooms.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service liveness."""
    return {
        "status": "healthy",
        "service": "Tourstay Portal API",
        "version": "1.0.0",
    }
