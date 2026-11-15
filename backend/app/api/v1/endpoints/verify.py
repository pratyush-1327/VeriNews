import hashlib
import json
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

router = APIRouter()


def compute_claim_hash(text: str) -> str:
    normalized = " ".join(text.lower().strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@router.post("", response_model=VerificationResponse, summary="Submit a claim for verification")
async def verify_claim(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    claim_input = request.text or request.url
    if not claim_input and not request.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'text', 'url', or 'image_base64' must be provided",
        )

    if not claim_input:
        claim_input = "Extracted claim from screenshot image"

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
        pass  # Redis failure shouldn't block verification

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
        # Populate Redis cache
        try:
            await redis.setex(
                cache_key,
                86400,
                json.dumps(
                    response_obj.model_dump(mode="json"), default=str
                ),
            )
        except Exception:
            pass
        return response_obj

    # 3. Phase 1 Mock/Skeleton (Ready for Phase 3 Gemini RAG Engine)
    # Provides initial validation and contract compliance
    new_dossier = VerificationDossier(
        id=uuid.uuid4(),
        claim_text=claim_input,
        claim_hash=claim_hash,
        verdict=ClaimVerdict.MISLEADING,
        truth_score=35.0,
        explanation_bullets=[
            "The circulating claim takes historical statements out of context.",
            "Official press releases confirm the policy was revised.",
            "Multiple accredited news wires reported the clarification.",
        ],
        evidence_sources=[
            {
                "title": "Press Information Bureau Clarification Note",
                "url": "https://pib.gov.in/factcheck",
                "publisher": "PIB Fact Check",
            },
            {
                "title": "Detailed Fact Check Report",
                "url": "https://www.thehindu.com/news/national",
                "publisher": "The Hindu",
            },
        ],
        debunk_card_url="/static/debunks/sample_card.png",
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

    # Store in Redis
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
