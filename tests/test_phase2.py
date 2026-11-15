import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1"


@pytest.mark.asyncio
async def test_ingestion_status():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        res = await client.get("/news/ingest/status")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_live_ingestion_and_feeds():
    # Allow generous timeout for live network scraping & Gemini calls
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Ingest Global feeds (limit to 1 article for speed)
        res_global_ingest = await client.post("/news/ingest?limit_per_source=1&scope=global")
        assert res_global_ingest.status_code == 200
        global_summary = res_global_ingest.json()
        assert global_summary["status"] == "completed"
        assert global_summary["sources_polled"] >= 1

        # 2. Ingest National feeds
        res_nat_ingest = await client.post("/news/ingest?limit_per_source=1&scope=national")
        assert res_nat_ingest.status_code == 200
        nat_summary = res_nat_ingest.json()
        assert nat_summary["status"] == "completed"

        # 3. Ingest City feed (Jaipur)
        res_city_ingest = await client.post("/news/ingest?limit_per_source=1&scope=city&city=jaipur")
        assert res_city_ingest.status_code == 200
        city_summary = res_city_ingest.json()
        assert city_summary["status"] == "completed"

        # 4. Check Global Feed
        feed_global = await client.get("/news/feed?scope=global")
        assert feed_global.status_code == 200
        global_articles = feed_global.json()["articles"]
        assert len(global_articles) > 0
        sample_art = global_articles[0]
        assert "summary_60_words" in sample_art
        assert "• " in sample_art["summary_60_words"]
        print(f"\n[Sample Global Article]:\nTitle: {sample_art['title']}\nSummary:\n{sample_art['summary_60_words']}")

        # 5. Check National Feed
        feed_nat = await client.get("/news/feed?scope=national")
        assert feed_nat.status_code == 200
        nat_articles = feed_nat.json()["articles"]
        assert len(nat_articles) > 0
        print(f"\n[Sample National Article]:\nTitle: {nat_articles[0]['title']}\nSummary:\n{nat_articles[0]['summary_60_words']}")

        # 6. Check Jaipur City Feed
        feed_jaipur = await client.get("/news/feed?scope=city&city=jaipur")
        assert feed_jaipur.status_code == 200
        jaipur_articles = feed_jaipur.json()["articles"]
        assert len(jaipur_articles) > 0
        assert jaipur_articles[0]["city_tag"] == "jaipur"
        print(f"\n[Sample Jaipur Article]:\nTitle: {jaipur_articles[0]['title']}\nSummary:\n{jaipur_articles[0]['summary_60_words']}")

        # 7. Test Deduplication: Re-running ingestion on Jaipur should skip all existing
        res_dedup = await client.post("/news/ingest?limit_per_source=1&scope=city&city=jaipur")
        assert res_dedup.status_code == 200
        dedup_summary = res_dedup.json()
        assert dedup_summary["duplicates_skipped"] >= 1
