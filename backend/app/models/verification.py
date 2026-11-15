import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, func, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import enum


class ClaimVerdict(str, enum.Enum):
    TRUE = "TRUE"
    MISLEADING = "MISLEADING"
    SATIRE = "SATIRE"
    FAKE = "FAKE"


class VerificationDossier(Base):
    __tablename__ = "verification_dossiers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    verdict: Mapped[ClaimVerdict] = mapped_column(
        SQLEnum(ClaimVerdict, name="verdict_enum"), nullable=False, index=True
    )
    truth_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_bullets: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence_sources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    debunk_card_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<VerificationDossier(verdict={self.verdict}, score={self.truth_score})>"
