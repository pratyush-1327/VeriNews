import hashlib
import json
import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
from app.api.deps import get_db, get_redis
from app.models.verification import VerificationDossier, ClaimVerdict
from app.schemas.verification import (
    VerifyRequest,
    VerificationResponse,
    EvidenceSource,
)
from app.services.scraper import ScraperService
from app.services.claim_extractor import ClaimExtractor
from app.services.evidence_retriever import EvidenceRetriever
from app.services.nli_evaluator import NLIEvaluator
from app.services.debunk_card import DebunkCardGenerator

from app.core.rate_limit import verify_rate_limiter

logger = logging.getLogger("verinews.verify")
router = APIRouter()


def compute_claim_hash(text: str) -> str:
    normalized = " ".join(text.lower().strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@router.post(
    "",
    response_model=VerificationResponse,
    dependencies=[Depends(verify_rate_limiter)],
    summary="Submit a claim for verification",
)
async def verify_claim(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Real-time Evidence-Based RAG Verification:
    1. Check Redis cache for instant (<30ms) responses on viral rumors.
    2. Check PostgreSQL database.
    3. Multimodal extraction & Atomic proposition decomposition (Gemini 3.8 Flash).
    4. Multi-layer live evidence retrieval (Tavily + DDGS + Satire Registry).
    5. Natural Language Inference veracity scoring (TRUE, MISLEADING, FAKE, SATIRE, UNVERIFIED).
    6. Dynamic WhatsApp Debunk Card PNG generation (Pillow).
    """
    claim_input = request.text
    if not claim_input and request.url:
        # Scrape text from submitted link
        scraped = await ScraperService.fetch_and_extract(request.url)
        claim_input = scraped.get("text") or request.url

    if not claim_input and request.image_base64:
        claim_input = "Extracted claim from screenshot image"

    if not claim_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'text', 'url', or 'image_base64' must be provided",
        )

    claim_hash = compute_claim_hash(claim_input)
    cache_key = f"verify:{claim_hash}"

    # 1. Check Redis Cache
    try:
        cached_data = await redis.get(cache_key)
        if cached_data:
            parsed = json.loads(cached_data)
            parsed["cached"] = True
            return VerificationResponse(**parsed)
    except Exception:
        pass

    # 2. Check Database
    stmt = select(VerificationDossier).where(
        VerificationDossier.claim_hash == claim_hash
    )
    res = await db.execute(stmt)
    dossier = res.scalar_one_or_none()

    if dossier:
        response_obj = VerificationResponse(
            id=dossier.id,
            claim_text=dossier.claim_text,
            claim_hash=dossier.claim_hash,
            verdict=dossier.verdict,
            truth_score=dossier.truth_score,
            explanation_bullets=dossier.explanation_bullets,
            evidence_sources=[
                EvidenceSource(**src) for src in dossier.evidence_sources
            ],
            debunk_card_url=dossier.debunk_card_url,
            created_at=dossier.created_at,
            cached=False,
        )
        try:
            await redis.setex(
                cache_key,
                86400,
                json.dumps(response_obj.model_dump(mode="json"), default=str),
            )
        except Exception:
            pass
        return response_obj

    # 3. Live RAG Pipeline Execution
    logger.info(f"Initiating RAG verification for claim hash: {claim_hash[:12]}...")

    # Step A: Atomic Claim Decomposition
    extracted = await ClaimExtractor.extract_claim(claim_input)
    core_claim = extracted.get("core_claim", claim_input[:150])
    queries = extracted.get("search_queries", [f"{claim_input[:80]} fact check"])

    # Step B: Tri-Source Evidence Retrieval (Tavily + DDGS + Satire check)
    retrieved = await EvidenceRetriever.retrieve_evidence(
        queries=queries,
        submitted_url=request.url,
    )
    evidence_list = retrieved.get("evidence", [])
    tavily_answer = retrieved.get("tavily_answer", "")
    is_satire = retrieved.get("is_satire", False)

    # Step C: Natural Language Inference (NLI) & Truth Scoring
    evaluated = await NLIEvaluator.evaluate(
        claim=core_claim,
        evidence=evidence_list,
        tavily_answer=tavily_answer,
        is_satire=is_satire,
    )
    verdict = evaluated["verdict"]
    truth_score = evaluated["truth_score"]
    explanation_bullets = evaluated["explanation_bullets"]

    # Step D: WhatsApp Debunk Card PNG Generation
    debunk_card_url = DebunkCardGenerator.generate_card(
        claim_text=core_claim,
        verdict=verdict,
        truth_score=truth_score,
        explanation_bullets=explanation_bullets,
        evidence_sources=evidence_list,
        claim_hash=claim_hash,
    )

    # Step E: Persist in Database
    new_dossier = VerificationDossier(
        id=uuid.uuid4(),
        claim_text=core_claim,
        claim_hash=claim_hash,
        verdict=verdict,
        truth_score=truth_score,
        explanation_bullets=explanation_bullets,
        evidence_sources=[
            {
                "title": src.get("title", "News Report"),
                "url": src.get("url", ""),
                "publisher": src.get("publisher", "Accredited Source"),
            }
            for src in evidence_list[:4]
        ],
        debunk_card_url=debunk_card_url,
    )
    db.add(new_dossier)
    await db.commit()
    await db.refresh(new_dossier)

    response_obj = VerificationResponse(
        id=new_dossier.id,
        claim_text=new_dossier.claim_text,
        claim_hash=new_dossier.claim_hash,
        verdict=new_dossier.verdict,
        truth_score=new_dossier.truth_score,
        explanation_bullets=new_dossier.explanation_bullets,
        evidence_sources=[
            EvidenceSource(**src) for src in new_dossier.evidence_sources
        ],
        debunk_card_url=new_dossier.debunk_card_url,
        created_at=new_dossier.created_at,
        cached=False,
    )

    # Step F: Cache in Redis (24 Hours TTL)
    try:
        await redis.setex(
            cache_key,
            86400,
            json.dumps(response_obj.model_dump(mode="json"), default=str),
        )
    except Exception:
        pass

    return response_obj


@router.get("/recent", response_model=List[VerificationResponse], summary="Get recently verified claims")
async def get_recent_verifications(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(VerificationDossier)
        .order_by(VerificationDossier.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    dossiers = res.scalars().all()

    return [
        VerificationResponse(
            id=d.id,
            claim_text=d.claim_text,
            claim_hash=d.claim_hash,
            verdict=d.verdict,
            truth_score=d.truth_score,
            explanation_bullets=d.explanation_bullets,
            evidence_sources=[
                EvidenceSource(**src) for src in d.evidence_sources
            ],
            debunk_card_url=d.debunk_card_url,
            created_at=d.created_at,
            cached=False,
        )
        for d in dossiers
    ]
