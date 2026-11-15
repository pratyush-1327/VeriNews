from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if not created (useful for dev and quick start)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown resources
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for VeriNews: AI-Powered Trusted News Feed & Fact Verification Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware (Allows Flutter Mobile, Web and Emulator access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
os.makedirs("static/debunks", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to VeriNews API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "version": settings.VERSION,
    }
