from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.source import NewsScope


class SourceBase(BaseModel):
    name: str
    rss_url: str
    default_scope: NewsScope = NewsScope.NATIONAL
    default_city_tag: str | None = None
    credibility_score: float = 100.0
    is_whitelisted: bool = True


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
