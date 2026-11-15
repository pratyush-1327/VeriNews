from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceResponse

router = APIRouter()


@router.get("", response_model=List[SourceResponse], summary="List all news sources")
async def list_sources(
    whitelisted_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Source)
    if whitelisted_only:
        query = query.where(Source.is_whitelisted == True)
    query = query.order_by(Source.name.asc())
    result = await db.execute(query)
    sources = result.scalars().all()
    return sources


@router.post(
    "",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new RSS news source",
)
async def create_source(
    source_in: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check if RSS URL already exists
    stmt = select(Source).where(Source.rss_url == source_in.rss_url)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source with this RSS URL already exists",
        )

    source = Source(**source_in.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source
