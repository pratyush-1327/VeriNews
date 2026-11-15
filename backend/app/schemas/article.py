from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.source import NewsScope


class ArticleBase(BaseModel):
    title: str
    summary_60_words: str
    url: str
    image_url: Optional[str] = None
    published_at: datetime
    scope: NewsScope
    city_tag: Optional[str] = None


class ArticleCreate(ArticleBase):
    source_id: UUID


class ArticleResponse(ArticleBase):
    id: UUID
    source_id: UUID
    created_at: datetime
    source_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleFeedResponse(BaseModel):
    scope: str
    city_tag: Optional[str] = None
    total: int
    articles: List[ArticleResponse]
