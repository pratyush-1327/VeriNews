import os
import pytest
from PIL import Image
from app.models.verification import ClaimVerdict
from app.services.debunk_card import DebunkCardGenerator


def test_debunk_card_generation_all_verdicts():
    verdicts = [
        ClaimVerdict.TRUE,
        ClaimVerdict.FAKE,
        ClaimVerdict.MISLEADING,
        ClaimVerdict.SATIRE,
        ClaimVerdict.UNVERIFIED,
    ]

    for v in verdicts:
        claim_hash = f"test_hash_{v.value.lower()}"
        card_url = DebunkCardGenerator.generate_card(
            claim_text="UNESCO declares Indian National Anthem the best in the world for 2026",
            verdict=v,
            truth_score=85.0 if v == ClaimVerdict.TRUE else (15.0 if v == ClaimVerdict.FAKE else 50.0),
            explanation_bullets=[
                "Official statements from UNESCO confirm no such ranking exists.",
                "The message has been circulated as a recurring viral hoax since 2008.",
                "Accredited fact-checkers like Snopes and BoomLive have repeatedly debunked it.",
            ],
            evidence_sources=[
                {"publisher": "Times of India Fact Check", "url": "https://timesofindia.indiatimes.com"},
                {"publisher": "Snopes", "url": "https://snopes.com"},
            ],
            claim_hash=claim_hash,
        )

        file_path = f"static/debunks/{claim_hash}.png"
        assert os.path.exists(file_path)
        with Image.open(file_path) as img:
            assert img.size == (1080, 1350)
            assert img.format == "PNG"

        print(f"[OK] Generated {v.value} card: {card_url} (1080x1350 PNG)")
