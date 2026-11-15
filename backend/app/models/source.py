import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class NewsScope(str, enum.Enum):
    GLOBAL = "global"
    NATIONAL = "national"
    CITY = "city"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rss_url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    default_scope: Mapped[NewsScope] = mapped_column(
        SQLEnum(NewsScope, name="news_scope_enum"),
        nullable=False,
        default=NewsScope.NATIONAL,
    )
    default_city_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, default=100.0)
    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    articles = relationship(
        "Article", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Source(name={self.name}, scope={self.default_scope}, city={self.default_city_tag})>"
