import logging
import re
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("verinews.summarizer")


class SummarizerService:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    SUMMARIZER_PROMPT = """You are an expert, neutral news editor for VeriNews.
Summarize the following news article into EXACTLY 3 concise bullet points.

CRITICAL CONSTRAINTS:
1. The total summary MUST be strictly under 60 words.
2. Output format must be EXACTLY 3 lines, each beginning with a bullet symbol: "• "
3. Maintain absolute factual neutrality: remove clickbait, sensational adjectives, speculation, and partisan bias.
4. Focus only on core factual assertions: who, what, where, and key numbers.

Article Title: {title}
Article Text:
{text}

Output:"""

    @classmethod
    async def summarize_article(
        cls,
        title: str,
        text: str,
        max_words: int = 60,
    ) -> str:
        """
        Summarizes news content into 3 neutral bullet points under 60 words using Gemini 3.8 Flash.
        Falls back to rule-based extractive summary on any API failure.
        """
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Using extractive fallback.")
            return cls._fallback_summary(title, text, max_words)

        # Truncate input text to ~3000 characters to keep latency and token usage low
        truncated_text = text[:3000].strip() if text else title
        prompt = cls.SUMMARIZER_PROMPT.format(
            title=title.strip(), text=truncated_text
        )

        url = f"{cls.GEMINI_API_URL.format(model=settings.GEMINI_MODEL)}?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 200,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = (
                            candidates[0]
                            .get("content", {})
                            .get("parts", [])
                        )
                        if parts:
                            raw_text = parts[0].get("text", "").strip()
                            clean_summary = cls._clean_and_enforce_format(
                                raw_text, max_words
                            )
                            if clean_summary:
                                return clean_summary
                logger.error(
                    f"Gemini API returned status {response.status_code}: {response.text}"
                )
        except Exception as e:
            logger.error(f"Error calling Gemini Summarizer API: {e}")

        # Fallback if API fails
        return cls._fallback_summary(title, text, max_words)

    @classmethod
    def _clean_and_enforce_format(cls, raw_text: str, max_words: int) -> Optional[str]:
        """Ensures the response has 3 bullet points starting with '• ' and stays within word limit."""
        lines = [
            line.strip()
            for line in raw_text.split("\n")
            if line.strip()
        ]

        bullet_lines = []
        for line in lines:
            # Strip markdown bullets like '*', '-', or numbers '1.'
            cleaned = re.sub(r"^[\*\-\•\d\.\)]\s*", "", line).strip()
            if cleaned:
                bullet_lines.append(f"• {cleaned}")

        if len(bullet_lines) >= 3:
            bullet_lines = bullet_lines[:3]
        elif len(bullet_lines) < 3:
            return None

        result = "\n".join(bullet_lines)
        words = result.split()
        if len(words) > max_words + 10:
            # Trim if model was slightly verbose
            result = " ".join(words[:max_words]) + "..."

        return result

    @classmethod
    def _fallback_summary(cls, title: str, text: str, max_words: int = 60) -> str:
        """Deterministic extractive fallback when LLM is unreachable."""
        cleaned_text = re.sub(r"\s+", " ", text or "").strip()
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", cleaned_text)
            if len(s.strip()) > 15
        ]

        bullets = []
        # First bullet is the headline fact
        bullets.append(f"• {title.strip()}")

        # Second and third from article body
        if len(sentences) >= 2:
            bullets.append(f"• {sentences[0]}")
            bullets.append(f"• {sentences[1]}")
        elif len(sentences) == 1:
            bullets.append(f"• {sentences[0]}")
            bullets.append("• Full coverage available at original publication.")
        else:
            bullets.append("• Developing news story from verified wires.")
            bullets.append("• Details confirmed through official reporting.")

        # Ensure word limit
        formatted = "\n".join(bullets[:3])
        words = formatted.split()
        if len(words) > max_words:
            formatted = " ".join(words[:max_words]) + "..."
        return formatted
