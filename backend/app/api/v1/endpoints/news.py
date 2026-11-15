from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api.deps import get_db
from app.models.source import NewsScope, Source
from app.models.article import Article
from app.schemas.article import ArticleFeedResponse, ArticleResponse, ArticleCreate
from app.core.config import settings

router = APIRouter()


@router.get("/cities", summary="Get supported city hubs with coordinates")
async def get_supported_cities() -> Dict[str, Any]:
    return {
        "cities": [
            {"id": tag, **meta} for tag, meta in settings.CITY_METADATA.items()
        ]
    }


@router.get("/feed", response_model=ArticleFeedResponse, summary="Get 60-word news feed")
async def get_news_feed(
    scope: NewsScope = Query(
        NewsScope.NATIONAL, description="Scope of news: global, national, or city"
    ),
    city: Optional[str] = Query(
        None,
        description="Required if scope=city. One of: delhi, jaipur, mumbai, bengaluru, chennai, kolkata",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    normalized_city = city.lower().strip() if city else None

    # Validate city if city scope is selected
    if scope == NewsScope.CITY:
        if not normalized_city:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query param 'city' is required when scope='city'. Supported: {settings.SUPPORTED_CITIES}",
            )
        if normalized_city not in settings.SUPPORTED_CITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"City '{normalized_city}' not supported. Choose from: {settings.SUPPORTED_CITIES}",
            )

    # Base query
    query = (
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.scope == scope)
    )

    if scope == NewsScope.CITY:
        query = query.where(Article.city_tag == normalized_city)

    # Count total
    count_query = select(func.count(Article.id)).where(Article.scope == scope)
    if scope == NewsScope.CITY:
        count_query = count_query.where(Article.city_tag == normalized_city)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Fetch paginated
    query = query.order_by(Article.published_at.desc()).offset(offset).limit(limit)
    res = await db.execute(query)
    articles_db = res.scalars().all()

    article_responses = [
        ArticleResponse(
            id=a.id,
            title=a.title,
            summary_60_words=a.summary_60_words,
            url=a.url,
            image_url=a.image_url,
            published_at=a.published_at,
            scope=a.scope,
            city_tag=a.city_tag,
            source_id=a.source_id,
            source_name=a.source.name if a.source else "Verified Source",
            created_at=a.created_at,
        )
        for a in articles_db
    ]

    return ArticleFeedResponse(
        scope=scope.value,
        city_tag=normalized_city,
        total=total,
        articles=article_responses,
    )


@router.post(
    "/article",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Insert a new article (used by ingestion engine)",
)
async def create_article(
    article_in: ArticleCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify source exists
    source = await db.get(Source, article_in.source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source ID not found",
        )

    # Check for duplicate URL
    stmt = select(Article).where(Article.url == article_in.url)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article with this URL already exists",
        )

    article = Article(**article_in.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)

    return ArticleResponse(
        id=article.id,
        title=article.title,
        summary_60_words=article.summary_60_words,
        url=article.url,
        image_url=article.image_url,
        published_at=article.published_at,
        scope=article.scope,
        city_tag=article.city_tag,
        source_id=article.source_id,
        source_name=source.name,
        created_at=article.created_at,
    )
