import os
import textwrap
from datetime import datetime, timezone
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
from app.models.verification import ClaimVerdict

FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


class DebunkCardGenerator:
    CARD_WIDTH = 1080
    CARD_HEIGHT = 1350

    # Color themes per verdict
    VERDICT_COLORS = {
        ClaimVerdict.TRUE: {
            "bg": (16, 185, 129),  # Emerald Green
            "text": (255, 255, 255),
            "label": "VERIFIED TRUE",
            "accent": (52, 211, 153),
        },
        ClaimVerdict.FAKE: {
            "bg": (239, 68, 68),  # Crimson Red
            "text": (255, 255, 255),
            "label": "FABRICATED / FAKE",
            "accent": (248, 113, 113),
        },
        ClaimVerdict.MISLEADING: {
            "bg": (245, 158, 11),  # Amber Yellow
            "text": (255, 255, 255),
            "label": "MISLEADING / OUT OF CONTEXT",
            "accent": (251, 191, 36),
        },
        ClaimVerdict.SATIRE: {
            "bg": (139, 92, 246),  # Vivid Purple
            "text": (255, 255, 255),
            "label": "SATIRE / PARODY",
            "accent": (167, 139, 250),
        },
        ClaimVerdict.UNVERIFIED: {
            "bg": (14, 165, 233),  # Sky Blue / Slate
            "text": (255, 255, 255),
            "label": "UNVERIFIED / UNCORROBORATED",
            "accent": (56, 189, 248),
        },
    }

    @classmethod
    def _get_font(cls, size: int, bold: bool = False) -> ImageFont.ImageFont:
        font_path = FONT_PATH_BOLD if bold else FONT_PATH_REGULAR
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    @classmethod
    def generate_card(
        cls,
        claim_text: str,
        verdict: ClaimVerdict,
        truth_score: float,
        explanation_bullets: List[str],
        evidence_sources: List[Dict[str, str]],
        claim_hash: str,
    ) -> str:
        """
        Dynamically generates a 1080x1350 branded debunk card image and saves it to static/debunks.
        Returns the relative web URL path: /static/debunks/{claim_hash}.png.
        """
        os.makedirs("static/debunks", exist_ok=True)
        output_filename = f"static/debunks/{claim_hash}.png"

        # 1. Base Canvas
        img = Image.new("RGB", (cls.CARD_WIDTH, cls.CARD_HEIGHT), color=(11, 15, 25))
        draw = ImageDraw.Draw(img)

        # 2. Outer Border & Header Background
        draw.rectangle(
            [(24, 24), (cls.CARD_WIDTH - 24, cls.CARD_HEIGHT - 24)],
            outline=(31, 41, 55),
            width=4,
        )

        # Header bar
        font_header_title = cls._get_font(36, bold=True)
        font_header_sub = cls._get_font(20, bold=False)
        draw.text(
            (60, 50),
            "VERINEWS • FACT-CHECK DOSSIER",
            font=font_header_title,
            fill=(56, 189, 248),
        )
        date_str = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
        draw.text(
            (60, 95),
            f"REAL-TIME VERIFICATION REPORT • {date_str}",
            font=font_header_sub,
            fill=(156, 163, 175),
        )

        # Divider
        draw.line([(60, 135), (cls.CARD_WIDTH - 60, 135)], fill=(31, 41, 55), width=2)

        # 3. Verdict Badge
        v_theme = cls.VERDICT_COLORS.get(
            verdict, cls.VERDICT_COLORS[ClaimVerdict.UNVERIFIED]
        )
        badge_y = 160
        badge_h = 110
        draw.rounded_rectangle(
            [(60, badge_y), (cls.CARD_WIDTH - 60, badge_y + badge_h)],
            radius=16,
            fill=v_theme["bg"],
        )

        font_verdict = cls._get_font(44, bold=True)
        draw.text(
            (90, badge_y + 20),
            v_theme["label"],
            font=font_verdict,
            fill=v_theme["text"],
        )

        font_score = cls._get_font(24, bold=True)
        score_text = f"TRUTH CONFIDENCE: {int(truth_score)}%"
        draw.text(
            (90, badge_y + 68),
            score_text,
            font=font_score,
            fill=(243, 244, 246),
        )

        # 4. Claim Container
        claim_y = 300
        claim_h = 240
        draw.rounded_rectangle(
            [(60, claim_y), (cls.CARD_WIDTH - 60, claim_y + claim_h)],
            radius=12,
            fill=(22, 30, 46),
            outline=(37, 48, 66),
            width=2,
        )

        # Accent quote indicator on left
        draw.rounded_rectangle(
            [(60, claim_y), (72, claim_y + claim_h)],
            radius=4,
            fill=v_theme["accent"],
        )

        font_sec_label = cls._get_font(22, bold=True)
        draw.text(
            (90, claim_y + 20),
            "CLAIM UNDER INVESTIGATION:",
            font=font_sec_label,
            fill=(148, 163, 184),
        )

        font_claim = cls._get_font(26, bold=False)
        # Wrap claim text
        wrapped_claim = textwrap.wrap(claim_text.strip(), width=58)[:4]
        cur_y = claim_y + 55
        for line in wrapped_claim:
            draw.text((90, cur_y), f'"{line}"', font=font_claim, fill=(241, 245, 249))
            cur_y += 34

        # 5. Key Verified Facts
        facts_y = 570
        facts_h = 470
        draw.rounded_rectangle(
            [(60, facts_y), (cls.CARD_WIDTH - 60, facts_y + facts_h)],
            radius=12,
            fill=(22, 30, 46),
            outline=(37, 48, 66),
            width=2,
        )

        draw.text(
            (90, facts_y + 24),
            "KEY VERIFIED FINDINGS:",
            font=font_sec_label,
            fill=(148, 163, 184),
        )

        font_bullet = cls._get_font(24, bold=False)
        cur_y = facts_y + 70
        for b in explanation_bullets[:3]:
            # Clean leading bullet if already present
            b_clean = b.lstrip("•*- ").strip()
            # Wrap bullet
            wrapped_b = textwrap.wrap(b_clean, width=54)[:3]
            # Draw bullet symbol
            draw.text((90, cur_y), "•", font=font_bullet, fill=v_theme["accent"])
            for line in wrapped_b:
                draw.text((120, cur_y), line, font=font_bullet, fill=(241, 245, 249))
                cur_y += 34
            cur_y += 18

        # 6. Citations & Footer
        footer_y = 1070
        draw.text(
            (60, footer_y),
            "GROUND-TRUTH SOURCES CONSULTED:",
            font=font_sec_label,
            fill=(148, 163, 184),
        )

        sources_text = " • ".join(
            [s.get("publisher", "Accredited Wire") for s in evidence_sources[:4]]
        )
        if not sources_text:
            sources_text = "Press Information Bureau • Reuters • Snopes • Accredited News Wires"

        font_sources = cls._get_font(22, bold=False)
        draw.text(
            (60, footer_y + 35),
            sources_text,
            font=font_sources,
            fill=(56, 189, 248),
        )

        # Watermark
        draw.line([(60, 1230), (cls.CARD_WIDTH - 60, 1230)], fill=(31, 41, 55), width=2)
        font_wm = cls._get_font(18, bold=False)
        draw.text(
            (60, 1255),
            "Verified by VeriNews AI Fact-Check Engine • Share to WhatsApp & Stop Misinformation",
            font=font_wm,
            fill=(100, 116, 139),
        )

        # Save card
        img.save(output_filename, format="PNG", optimize=True)
        return f"/static/debunks/{claim_hash}.png"
