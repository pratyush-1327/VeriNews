import os
import json
import logging
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import redis.asyncio as aioredis

from app.api.deps import get_db, get_redis, verify_admin_key
from app.models.verification import VerificationDossier, ClaimVerdict
from app.models.article import Article
from app.core.config import settings
from app.schemas.verification import VerificationResponse, EvidenceSource
from app.schemas.admin import (
    AdminClaimOverrideRequest,
    AdminClaimsListResponse,
    AdminStatsResponse,
)
from app.services.debunk_card import DebunkCardGenerator

logger = logging.getLogger("verinews.admin")
router = APIRouter(dependencies=[Depends(verify_admin_key)])


def _to_evidence_sources(sources_data: list) -> List[EvidenceSource]:
    items = []
    for src in sources_data:
        if isinstance(src, dict):
            items.append(
                EvidenceSource(
                    title=src.get("title", "Evidence Document"),
                    url=src.get("url", ""),
                    publisher=src.get("publisher", src.get("source_name", "Verified Publisher")),
                )
            )
    return items


@router.get("/stats", response_model=AdminStatsResponse, summary="Get fact-checking portal overview statistics")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
):
    """Returns platform metrics for fact-checkers."""
    # 1. Total claims count
    total_claims_res = await db.execute(select(func.count(VerificationDossier.id)))
    total_claims = total_claims_res.scalar() or 0

    # 2. Count by verdict
    verdict_stmt = select(
        VerificationDossier.verdict,
        func.count(VerificationDossier.id),
    ).group_by(VerificationDossier.verdict)
    verdict_res = await db.execute(verdict_stmt)
    claims_by_verdict = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): row[1]
        for row in verdict_res.all()
    }

    # Ensure all enum values exist in dictionary
    for v in ClaimVerdict:
        if v.value not in claims_by_verdict:
            claims_by_verdict[v.value] = 0

    # 3. Total articles count
    total_articles_res = await db.execute(select(func.count(Article.id)))
    total_articles = total_articles_res.scalar() or 0

    return AdminStatsResponse(
        total_claims=total_claims,
        claims_by_verdict=claims_by_verdict,
        total_articles=total_articles,
        supported_cities_count=len(settings.SUPPORTED_CITIES),
    )


@router.get("/claims", response_model=AdminClaimsListResponse, summary="List verified claims with filters")
async def list_admin_claims(
    verdict: Optional[ClaimVerdict] = Query(None, description="Filter by verdict class"),
    search: Optional[str] = Query(None, description="Search claim text"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List claims for human review and auditing."""
    query = select(VerificationDossier)
    count_query = select(func.count(VerificationDossier.id))

    if verdict:
        query = query.where(VerificationDossier.verdict == verdict)
        count_query = count_query.where(VerificationDossier.verdict == verdict)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.where(VerificationDossier.claim_text.ilike(search_filter))
        count_query = count_query.where(VerificationDossier.claim_text.ilike(search_filter))

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(desc(VerificationDossier.created_at)).offset(offset).limit(limit)
    res = await db.execute(query)
    dossiers = res.scalars().all()

    claim_responses = [
        VerificationResponse(
            id=d.id,
            claim_text=d.claim_text,
            claim_hash=d.claim_hash,
            verdict=d.verdict,
            truth_score=d.truth_score,
            explanation_bullets=d.explanation_bullets,
            evidence_sources=_to_evidence_sources(d.evidence_sources),
            debunk_card_url=d.debunk_card_url,
            created_at=d.created_at,
            cached=False,
        )
        for d in dossiers
    ]

    return AdminClaimsListResponse(
        total=total,
        claims=claim_responses,
    )


@router.get("/claims/{claim_id}", response_model=VerificationResponse, summary="Get single claim details")
async def get_claim_detail(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    dossier = await db.get(VerificationDossier, claim_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim ID {claim_id} not found",
        )

    return VerificationResponse(
        id=dossier.id,
        claim_text=dossier.claim_text,
        claim_hash=dossier.claim_hash,
        verdict=dossier.verdict,
        truth_score=dossier.truth_score,
        explanation_bullets=dossier.explanation_bullets,
        evidence_sources=_to_evidence_sources(dossier.evidence_sources),
        debunk_card_url=dossier.debunk_card_url,
        created_at=dossier.created_at,
        cached=False,
    )


@router.put("/claims/{claim_id}/override", response_model=VerificationResponse, summary="Human review override of claim verdict")
async def override_claim_verdict(
    claim_id: UUID,
    override: AdminClaimOverrideRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Overrides the AI-generated verdict and truth score:
    1. Updates PostgreSQL record.
    2. Re-generates Pillow PNG debunk card with human-verified verdict and bullets.
    3. Invalidates and refreshes the Redis cache key for instant propagation.
    """
    dossier = await db.get(VerificationDossier, claim_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim ID {claim_id} not found",
        )

    logger.info(
        f"Admin overriding Claim ID {claim_id}: {dossier.verdict} -> {override.verdict} "
        f"(Truth Score: {override.truth_score}%)"
    )

    # Update database fields
    dossier.verdict = override.verdict
    dossier.truth_score = override.truth_score
    dossier.explanation_bullets = override.explanation_bullets

    # Re-generate branded debunk card PNG
    try:
        new_card_url = DebunkCardGenerator.generate_card(
            claim_text=dossier.claim_text,
            verdict=override.verdict,
            truth_score=override.truth_score,
            explanation_bullets=override.explanation_bullets,
            evidence_sources=dossier.evidence_sources,
            claim_hash=dossier.claim_hash,
        )
        dossier.debunk_card_url = new_card_url
    except Exception as e:
        logger.error(f"Failed to regenerate debunk card: {e}")

    await db.commit()
    await db.refresh(dossier)

    response_obj = VerificationResponse(
        id=dossier.id,
        claim_text=dossier.claim_text,
        claim_hash=dossier.claim_hash,
        verdict=dossier.verdict,
        truth_score=dossier.truth_score,
        explanation_bullets=dossier.explanation_bullets,
        evidence_sources=_to_evidence_sources(dossier.evidence_sources),
        debunk_card_url=dossier.debunk_card_url,
        created_at=dossier.created_at,
        cached=False,
    )

    # Invalidate and update Redis cache
    cache_key = f"verify:{dossier.claim_hash}"
    try:
        await redis.setex(
            cache_key,
            86400,
            json.dumps(response_obj.model_dump(mode="json"), default=str),
        )
    except Exception as e:
        logger.error(f"Failed to update Redis cache key {cache_key}: {e}")

    return response_obj


@router.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a claim from registry")
async def delete_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    dossier = await db.get(VerificationDossier, claim_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim ID {claim_id} not found",
        )

    # Remove image file if exists
    if dossier.debunk_card_url:
        local_path = dossier.debunk_card_url.lstrip("/")
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

    # Invalidate Redis cache
    cache_key = f"verify:{dossier.claim_hash}"
    try:
        await redis.delete(cache_key)
    except Exception:
        pass

    await db.delete(dossier)
    await db.commit()
    return None
