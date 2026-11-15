from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api.v1.router import api_router
from app.services.seed import seed_default_sources
from app.services.ingestion import IngestionService

logger = logging.getLogger("verinews.main")
scheduler = AsyncIOScheduler()


async def scheduled_ingestion_job():
    """Periodic job running every 30 minutes to fetch fresh news."""
    logger.info("Executing scheduled news ingestion...")
    async with AsyncSessionLocal() as session:
        try:
            await IngestionService.run_ingestion(db=session, limit_per_source=5)
        except Exception as e:
            logger.error(f"Error during scheduled ingestion: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables if not created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seed default verified sources
    async with AsyncSessionLocal() as session:
        await seed_default_sources(session)

    # 3. Start periodic background scheduler
    scheduler.add_job(
        scheduled_ingestion_job,
        "interval",
        minutes=30,
        id="rss_ingestion_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Started APScheduler background news ingestion job (30-min interval).")

    yield

    # 4. Graceful shutdown
    scheduler.shutdown(wait=False)
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
