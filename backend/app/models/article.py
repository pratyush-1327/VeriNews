import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.source import NewsScope


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary_60_words: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    scope: Mapped[NewsScope] = mapped_column(
        SQLEnum(NewsScope, name="news_scope_enum"),
        nullable=False,
        index=True,
    )
    city_tag: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    source = relationship("Source", back_populates="articles")

    def __repr__(self) -> str:
        return f"<Article(title={self.title[:30]}..., scope={self.scope}, city={self.city_tag})>"
