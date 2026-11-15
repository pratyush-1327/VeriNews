from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.models.verification import ClaimVerdict
from app.schemas.verification import VerificationResponse


class AdminClaimOverrideRequest(BaseModel):
    verdict: ClaimVerdict = Field(..., description="Overridden verdict class")
    truth_score: int = Field(..., ge=0, le=100, description="Overridden truth score (0-100)")
    explanation_bullets: List[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Updated 2-3 takeaway facts for the claim",
    )
    reviewer_notes: Optional[str] = Field(
        None,
        description="Optional audit notes on why the verdict was changed",
    )


class AdminClaimsListResponse(BaseModel):
    total: int
    claims: List[VerificationResponse]


class AdminStatsResponse(BaseModel):
    total_claims: int
    claims_by_verdict: Dict[str, int]
    total_articles: int
    supported_cities_count: int
