import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.source import Source, NewsScope

logger = logging.getLogger("verinews.seed")

DEFAULT_SOURCES = [
    # Global
    {
        "name": "BBC World News",
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "default_scope": NewsScope.GLOBAL,
        "default_city_tag": None,
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
    {
        "name": "Al Jazeera World",
        "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "default_scope": NewsScope.GLOBAL,
        "default_city_tag": None,
        "credibility_score": 95.0,
        "is_whitelisted": True,
    },
    # National (India)
    {
        "name": "The Hindu National",
        "rss_url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "default_scope": NewsScope.NATIONAL,
        "default_city_tag": None,
        "credibility_score": 99.0,
        "is_whitelisted": True,
    },
    {
        "name": "Times of India India",
        "rss_url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "default_scope": NewsScope.NATIONAL,
        "default_city_tag": None,
        "credibility_score": 94.0,
        "is_whitelisted": True,
    },
    {
        "name": "NDTV Top Stories",
        "rss_url": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "default_scope": NewsScope.NATIONAL,
        "default_city_tag": None,
        "credibility_score": 95.0,
        "is_whitelisted": True,
    },
    # 6 Target Cities
    {
        "name": "The Hindu Delhi",
        "rss_url": "https://www.thehindu.com/news/cities/Delhi/feeder/default.rss",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "delhi",
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
    {
        "name": "Times of India Jaipur",
        "rss_url": "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "jaipur",
        "credibility_score": 95.0,
        "is_whitelisted": True,
    },
    {
        "name": "The Hindu Mumbai",
        "rss_url": "https://www.thehindu.com/news/cities/mumbai/feeder/default.rss",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "mumbai",
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
    {
        "name": "The Hindu Bengaluru",
        "rss_url": "https://www.thehindu.com/news/cities/bangalore/feeder/default.rss",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "bengaluru",
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
    {
        "name": "The Hindu Chennai",
        "rss_url": "https://www.thehindu.com/news/cities/chennai/feeder/default.rss",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "chennai",
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
    {
        "name": "The Hindu Kolkata",
        "rss_url": "https://www.thehindu.com/news/cities/kolkata/feeder/default.rss",
        "default_scope": NewsScope.CITY,
        "default_city_tag": "kolkata",
        "credibility_score": 98.0,
        "is_whitelisted": True,
    },
]


async def seed_default_sources(db: AsyncSession) -> int:
    """
    Seeds initial whitelisted sources if they don't already exist.
    Returns count of added sources.
    """
    added_count = 0
    for src_data in DEFAULT_SOURCES:
        stmt = select(Source).where(Source.rss_url == src_data["rss_url"])
        existing = await db.execute(stmt)
        if not existing.scalar_one_or_none():
            source = Source(**src_data)
            db.add(source)
            added_count += 1

    if added_count > 0:
        await db.commit()
        logger.info(f"Seeded {added_count} default news sources.")

    return added_count
