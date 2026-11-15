from fastapi import APIRouter
from app.api.v1.endpoints import health, sources, news, verify

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(news.router, prefix="/news", tags=["News Feed"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(verify.router, prefix="/verify", tags=["Verification"])
