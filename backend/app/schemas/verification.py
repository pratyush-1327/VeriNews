from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.verification import ClaimVerdict


class EvidenceSource(BaseModel):
    title: str
    url: str
    publisher: str


class VerifyRequest(BaseModel):
    text: Optional[str] = Field(
        None, description="Viral claim, WhatsApp forward, or text to verify"
    )
    url: Optional[str] = Field(None, description="News link to verify")
    image_base64: Optional[str] = Field(
        None, description="Base64 encoded screenshot image (optional)"
    )


class VerificationResponse(BaseModel):
    id: UUID
    claim_text: str
    claim_hash: str
    verdict: ClaimVerdict
    truth_score: float
    explanation_bullets: List[str]
    evidence_sources: List[EvidenceSource]
    debunk_card_url: Optional[str] = None
    created_at: datetime
    cached: bool = False

    model_config = ConfigDict(from_attributes=True)
