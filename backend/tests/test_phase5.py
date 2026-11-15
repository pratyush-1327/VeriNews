import pytest
import os
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.core.ssrf import validate_url_ssrf

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_ssrf_protection_unit():
    """Verify SSRF validator blocks private, loopback, metadata, and invalid schemes."""
    # 1. Block loopback
    with pytest.raises(HTTPException) as exc:
        await validate_url_ssrf("http://127.0.0.1:8000/admin")
    assert exc.value.status_code == 400
    assert "SSRF Blocked" in exc.value.detail

    # 2. Block localhost hostname
    with pytest.raises(HTTPException) as exc:
        await validate_url_ssrf("http://localhost:5432")
    assert exc.value.status_code == 400

    # 3. Block AWS/Cloud metadata IP
    with pytest.raises(HTTPException) as exc:
        await validate_url_ssrf("http://169.254.169.254/latest/meta-data")
    assert exc.value.status_code == 400

    # 4. Block RFC 1918 private subnets
    for private_url in [
        "http://10.0.0.5/secrets",
        "http://192.168.1.1/router",
        "http://172.16.0.10:8080",
    ]:
        with pytest.raises(HTTPException) as exc:
            await validate_url_ssrf(private_url)
        assert exc.value.status_code == 400

    # 5. Block non-HTTP schemes
    for bad_scheme in ["file:///etc/passwd", "ftp://example.com/file", "gopher://evil.com"]:
        with pytest.raises(HTTPException) as exc:
            await validate_url_ssrf(bad_scheme)
        assert exc.value.status_code == 400

    # 6. Public reputable websites pass
    clean_url = await validate_url_ssrf("https://www.reuters.com/world")
    assert clean_url == "https://www.reuters.com/world"


@pytest.mark.asyncio
async def test_verify_ssrf_endpoint_protection():
    """Verify POST /api/v1/verify rejects malicious internal URLs with HTTP 400."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.post(
            "/api/v1/verify",
            json={"url": "http://127.0.0.1:8000/internal-leak"},
        )
        assert res.status_code == 400
        assert "SSRF Blocked" in res.json()["detail"]


@pytest.mark.asyncio
async def test_admin_auth_protection():
    """Verify admin endpoints require valid X-Admin-Key header."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # No key -> 403
        res = await client.get("/api/v1/admin/stats")
        assert res.status_code == 403

        # Invalid key -> 403
        res = await client.get(
            "/api/v1/admin/stats",
            headers={"X-Admin-Key": "wrong-secret-key"},
        )
        assert res.status_code == 403

        # Valid key -> 200
        res = await client.get(
            "/api/v1/admin/stats",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
        )
        assert res.status_code == 200
        data = res.json()
        assert "total_claims" in data
        assert "claims_by_verdict" in data
        assert "total_articles" in data


@pytest.mark.asyncio
async def test_admin_claim_override_and_cache_invalidation():
    """
    Test human fact-checker overriding an AI verdict:
    1. Fetch an existing verified claim from registry.
    2. Admin overrides verdict to TRUE with 95% truth score and facts.
    3. Verify debunk card PNG is regenerated on disk.
    4. Verify GET /api/v1/admin/claims/{claim_id} serves the updated record.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Fetch recent claims
        recents_res = await client.get("/api/v1/verify/recent?limit=1")
        assert recents_res.status_code == 200
        recents = recents_res.json()
        assert len(recents) > 0

        target = recents[0]
        claim_id = target["id"]

        # 2. Human fact-checker overrides verdict
        override_payload = {
            "verdict": "TRUE",
            "truth_score": 95,
            "explanation_bullets": [
                "Official verified fact statement from fact-checking board.",
                "Primary source documentation confirmed authentic.",
                "Entailment validated by accredited editorial team.",
            ],
            "reviewer_notes": "Reviewed and confirmed by senior fact checker.",
        }

        override_res = await client.put(
            f"/api/v1/admin/claims/{claim_id}/override",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
            json=override_payload,
        )
        assert override_res.status_code == 200
        updated = override_res.json()
        assert updated["verdict"] == "TRUE"
        assert updated["truth_score"] == 95
        assert len(updated["explanation_bullets"]) == 3

        # 3. Check card file exists on disk
        card_file = updated["debunk_card_url"].lstrip("/")
        assert os.path.exists(card_file)

        # 4. Verify GET /api/v1/admin/claims/{claim_id} serves the updated record
        get_res = await client.get(
            f"/api/v1/admin/claims/{claim_id}",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
        )
        assert get_res.status_code == 200
        v_data = get_res.json()
        assert v_data["verdict"] == "TRUE"
        assert v_data["truth_score"] == 95


@pytest.mark.asyncio
async def test_admin_claim_list_and_delete():
    """Verify admin claim listing with filters and deletion."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # List claims
        list_res = await client.get(
            "/api/v1/admin/claims?limit=20",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
        )
        assert list_res.status_code == 200
        data = list_res.json()
        assert data["total"] >= 1
        claims = data["claims"]
        assert len(claims) > 0

        # Delete the last claim in list
        claim_to_delete = claims[-1]
        claim_id = claim_to_delete["id"]

        del_res = await client.delete(
            f"/api/v1/admin/claims/{claim_id}",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
        )
        assert del_res.status_code == 204

        # Confirm 404
        get_res = await client.get(
            f"/api/v1/admin/claims/{claim_id}",
            headers={"X-Admin-Key": settings.ADMIN_SECRET_KEY},
        )
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_admin_portal_web_route():
    """Verify GET /admin serves the HTML review portal."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        res = await client.get("/admin")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "VeriNews" in res.text
        assert "Fact-Checker Review Portal" in res.text
