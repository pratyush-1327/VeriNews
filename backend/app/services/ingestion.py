import asyncio
import logging
from datetime import datetime, timezone
import time
from typing import Dict, Any, Optional, List
import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.source import Source, NewsScope
from app.models.article import Article
from app.services.scraper import ScraperService
from app.services.summarizer import SummarizerService
from app.services.classifier import CityClassifier

logger = logging.getLogger("verinews.ingestion")

# In-memory latest run statistics
LATEST_INGESTION_STATUS: Dict[str, Any] = {
    "status": "idle",
    "last_run": None,
    "duration_seconds": 0.0,
    "articles_added": 0,
    "duplicates_skipped": 0,
    "errors": 0,
}


class IngestionService:
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    }

    @classmethod
    async def run_ingestion(
        cls,
        db: AsyncSession,
        limit_per_source: int = 5,
        scope_filter: Optional[NewsScope] = None,
        city_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Polls whitelisted sources, parses RSS, scrapes full article text,
        generates 60-word 3-bullet summaries via Gemini, tags scope/city, and persists.
        """
        global LATEST_INGESTION_STATUS
        start_time = time.time()
        LATEST_INGESTION_STATUS["status"] = "running"

        query = select(Source).where(Source.is_whitelisted == True)
        if scope_filter:
            query = query.where(Source.default_scope == scope_filter)
        if city_filter:
            query = query.where(Source.default_city_tag == city_filter.lower())

        result = await db.execute(query)
        sources: List[Source] = list(result.scalars().all())

        articles_added = 0
        duplicates_skipped = 0
        errors = 0

        logger.info(f"Starting ingestion across {len(sources)} sources...")

        async with httpx.AsyncClient(headers=cls.HEADERS, timeout=12.0) as http_client:
            for source in sources:
                try:
                    # Fetch RSS XML
                    resp = await http_client.get(source.rss_url)
                    if resp.status_code != 200:
                        logger.warning(
                            f"Failed to fetch feed {source.name} ({resp.status_code})"
                        )
                        errors += 1
                        continue

                    # Parse feed
                    feed = feedparser.parse(resp.text)
                    entries = feed.entries[:limit_per_source]

                    for entry in entries:
                        url = getattr(entry, "link", None)
                        title = getattr(entry, "title", None)

                        if not url or not title:
                            continue

                        # 1. Deduplication check against DB
                        stmt = select(Article.id).where(Article.url == url)
                        check = await db.execute(stmt)
                        if check.scalar_one_or_none():
                            duplicates_skipped += 1
                            continue

                        # 2. Extract publication time
                        pub_date = datetime.now(timezone.utc)
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            pub_date = datetime.fromtimestamp(
                                time.mktime(entry.published_parsed), tz=timezone.utc
                            )

                        fallback_summary = getattr(entry, "summary", "")

                        # 3. Scrape full content using trafilatura
                        scraped = await ScraperService.fetch_and_extract(
                            url=url,
                            fallback_title=title,
                            fallback_summary=fallback_summary,
                        )

                        # 4. Generate 60-word neutral 3-bullet summary via Gemini
                        summary_60 = await SummarizerService.summarize_article(
                            title=title,
                            text=scraped["text"],
                        )

                        # 5. Classify scope and city tag
                        final_scope, final_city = CityClassifier.classify(
                            title=title,
                            text=scraped["text"],
                            source=source,
                        )

                        # 6. Save article
                        article = Article(
                            title=title.strip(),
                            summary_60_words=summary_60,
                            source_id=source.id,
                            url=url.strip(),
                            image_url=scraped.get("image_url"),
                            published_at=pub_date,
                            scope=final_scope,
                            city_tag=final_city,
                        )
                        db.add(article)
                        await db.commit()
                        articles_added += 1
                        logger.info(
                            f"Ingested [{final_scope.value.upper()}:{final_city or 'ALL'}] {title[:40]}..."
                        )

                except Exception as e:
                    logger.error(f"Error processing source {source.name}: {e}")
                    errors += 1

        duration = round(time.time() - start_time, 2)
        summary_result = {
            "status": "completed",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "sources_polled": len(sources),
            "articles_added": articles_added,
            "duplicates_skipped": duplicates_skipped,
            "errors": errors,
        }
        LATEST_INGESTION_STATUS.update(summary_result)
        return summary_result
