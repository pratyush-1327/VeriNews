import time
import uuid
import pytest
import httpx

BASE_URL = "http://localhost:8000/api/v1"


@pytest.mark.asyncio
async def test_verify_fake_viral_hoax():
    """Tests verification of a known debunked viral rumor."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "text": "Breaking viral forward: UNESCO has just declared the Indian National Anthem as the best in the world."
        }
        res = await client.post("/verify", json=payload)
        assert res.status_code == 200
        data = res.json()
        print(f"\n[Fake Claim Result]: Verdict={data['verdict']}, Score={data['truth_score']}%")
        for b in data["explanation_bullets"]:
            print(f"  {b}")
        print(f"Debunk Card: {data['debunk_card_url']}")

        assert data["verdict"] in ["FAKE", "MISLEADING"]
        assert data["truth_score"] <= 35.0
        assert len(data["explanation_bullets"]) == 3
        assert data["debunk_card_url"].startswith("/static/debunks/")


@pytest.mark.asyncio
async def test_verify_true_historical_fact():
    """Tests verification of a verified true event."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "text": "India's Chandrayaan-3 achieved a historic soft landing on the south pole of the Moon in August 2023."
        }
        res = await client.post("/verify", json=payload)
        assert res.status_code == 200
        data = res.json()
        print(f"\n[True Claim Result]: Verdict={data['verdict']}, Score={data['truth_score']}%")
        for b in data["explanation_bullets"]:
            print(f"  {b}")
        print(f"Debunk Card: {data['debunk_card_url']}")

        assert data["verdict"] == "TRUE"
        assert data["truth_score"] >= 80.0
        assert len(data["explanation_bullets"]) == 3
        assert data["debunk_card_url"].startswith("/static/debunks/")


@pytest.mark.asyncio
async def test_verify_unverified_emergent_rumor():
    """Tests the new UNVERIFIED classification for uncorroborated, novel claims."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "text": f"Local resident committee in Sector 9 Jaipur reported a private neighborhood gardening workshop scheduled for next Tuesday {uuid.uuid4().hex[:6]}."
        }
        res = await client.post("/verify", json=payload)
        assert res.status_code == 200
        data = res.json()
        print(f"\n[Unverified Claim Result]: Verdict={data['verdict']}, Score={data['truth_score']}%")
        for b in data["explanation_bullets"]:
            print(f"  {b}")
        print(f"Debunk Card: {data['debunk_card_url']}")

        assert data["verdict"] == "UNVERIFIED"
        assert len(data["explanation_bullets"]) == 3
        assert data["debunk_card_url"].startswith("/static/debunks/")


@pytest.mark.asyncio
async def test_redis_claim_caching():
    """Tests that duplicate viral claims are returned instantly from Redis cache."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "text": "Government announces free electricity for all citizens starting next month on social media."
        }
        # First call (cold run)
        res1 = await client.post("/verify", json=payload)
        assert res1.status_code == 200
        data1 = res1.json()

        # Second call (hot cache run)
        start_time = time.time()
        res2 = await client.post("/verify", json=payload)
        latency_ms = (time.time() - start_time) * 1000
        assert res2.status_code == 200
        data2 = res2.json()

        print(f"\n[Cache Test]: Cold call completed. Hot call latency: {latency_ms:.2f}ms (cached={data2['cached']})")
        assert data2["cached"] is True
        assert data2["claim_hash"] == data1["claim_hash"]
        assert latency_ms < 100.0  # Must be sub-100ms
