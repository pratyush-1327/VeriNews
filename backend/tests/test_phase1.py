import uuid
from datetime import datetime, timezone
import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1"


@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "healthy"
        assert data["redis"] == "healthy"


@pytest.mark.asyncio
async def test_supported_cities():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/news/cities")
        assert response.status_code == 200
        data = response.json()
        city_ids = [c["id"] for c in data["cities"]]
        assert "delhi" in city_ids
        assert "jaipur" in city_ids
        assert "mumbai" in city_ids
        assert "bengaluru" in city_ids
        assert "chennai" in city_ids
        assert "kolkata" in city_ids


@pytest.mark.asyncio
async def test_create_source_and_articles():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Create a source
        source_payload = {
            "name": "The Hindu Test Wire",
            "rss_url": "https://www.thehindu.com/test-feed.rss",
            "default_scope": "national",
            "default_city_tag": None,
            "credibility_score": 98.5,
            "is_whitelisted": True,
        }
        res_src = await client.post("/sources", json=source_payload)
        # If already exists from previous run, ignore 400
        if res_src.status_code == 201:
            source_id = res_src.json()["id"]
        else:
            sources = (await client.get("/sources")).json()
            source_id = sources[0]["id"]

        now_iso = datetime.now(timezone.utc).isoformat()

        # 2. Insert Mumbai article
        mumbai_art = {
            "title": "Mumbai Metro Line 3 Begins Full Commercial Operations",
            "summary_60_words": "• Phase 1 of underground Metro Line 3 opened to commuters today.\n• The corridor connects SEEPZ to BKC reducing road congestion.\n• Daily ridership is expected to exceed 400,000 passengers.",
            "source_id": source_id,
            "url": f"https://www.thehindu.com/news/cities/mumbai/metro-line-3-test-article-{uuid.uuid4().hex[:6]}",
            "published_at": now_iso,
            "scope": "city",
            "city_tag": "mumbai",
        }
        await client.post("/news/article", json=mumbai_art)

        # 3. Insert Delhi article
        delhi_art = {
            "title": "Delhi Launches New EV Bus Fleet for Clean Public Transit",
            "summary_60_words": "• 500 new zero-emission electric buses flagged off in the capital.\n• Routes prioritize high-density university and commercial hubs.\n• Air quality monitoring sensors integrated on each vehicle.",
            "source_id": source_id,
            "url": f"https://www.thehindu.com/news/cities/delhi/ev-bus-fleet-test-article-{uuid.uuid4().hex[:6]}",
            "published_at": now_iso,
            "scope": "city",
            "city_tag": "delhi",
        }
        await client.post("/news/article", json=delhi_art)

        # 4. Fetch Mumbai feed
        res_mumbai = await client.get("/news/feed?scope=city&city=mumbai&limit=50")
        assert res_mumbai.status_code == 200
        mumbai_data = res_mumbai.json()
        assert mumbai_data["city_tag"] == "mumbai"
        assert any(
            "Mumbai Metro" in a["title"] for a in mumbai_data["articles"]
        )
        assert not any(
            "Delhi Launches" in a["title"] for a in mumbai_data["articles"]
        )

        # 5. Fetch Delhi feed
        res_delhi = await client.get("/news/feed?scope=city&city=delhi&limit=50")
        assert res_delhi.status_code == 200
        delhi_data = res_delhi.json()
        assert delhi_data["city_tag"] == "delhi"
        assert any(
            "Delhi Launches" in a["title"] for a in delhi_data["articles"]
        )


@pytest.mark.asyncio
async def test_city_validation():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Missing city when scope=city
        res = await client.get("/news/feed?scope=city")
        assert res.status_code == 400

        # Unsupported city
        res = await client.get("/news/feed?scope=city&city=atlantis")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_verification_and_caching():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        claim_payload = {
            "text": "Breaking: UNESCO declares Indian National Anthem the best in the world for 2026",
        }

        # 1. First verification request
        res1 = await client.post("/verify", json=claim_payload)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["verdict"] in ["TRUE", "MISLEADING", "SATIRE", "FAKE"]
        assert len(data1["explanation_bullets"]) == 3
        assert len(data1["evidence_sources"]) >= 1

        # 2. Second verification request (identical text) -> Should hit Redis cache
        res2 = await client.post("/verify", json=claim_payload)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["cached"] is True
        assert data2["claim_hash"] == data1["claim_hash"]
