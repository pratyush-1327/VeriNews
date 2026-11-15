import json
import logging
import re
from typing import Dict, Any, List
import httpx
from app.core.config import settings

logger = logging.getLogger("verinews.claim_extractor")


class ClaimExtractor:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    EXTRACTION_PROMPT = """You are an expert fact-checking intelligence analyst.
Analyze the following input (which may be a viral WhatsApp forward, rumor, tweet, or news headline):

INPUT TEXT:
\"\"\"{text}\"\"\"

TASKS:
1. Extract the single core factual claim proposition (strip all clickbait, emotional rhetoric, exclamation marks, and emojis).
2. Generate 2 to 3 targeted web search queries specifically designed to find accredited debunks, official statements, or news reports regarding this claim.

OUTPUT STRICTLY AS VALID JSON with this exact structure (no markdown fences, just JSON):
{{
  "core_claim": "Clear, declarative sentence stating the core assertion.",
  "search_queries": [
    "query 1 fact check",
    "query 2 official confirmation"
  ]
}}"""

    @classmethod
    async def extract_claim(cls, text: str) -> Dict[str, Any]:
        """
        Decomposes messy input into an atomic claim proposition and search queries.
        """
        cleaned_input = text.strip()
        if not settings.GEMINI_API_KEY or len(cleaned_input) < 10:
            return cls._fallback_extraction(cleaned_input)

        prompt = cls.EXTRACTION_PROMPT.format(text=cleaned_input[:2000])
        models_to_try = [
            settings.GEMINI_MODEL,
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
        ]

        async with httpx.AsyncClient(timeout=8.0) as client:
            for model_name in models_to_try:
                url = f"{cls.GEMINI_API_URL.format(model=model_name)}?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                }

                try:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                raw_json = parts[0].get("text", "").strip()
                                parsed = json.loads(raw_json)
                                if "core_claim" in parsed and "search_queries" in parsed:
                                    return {
                                        "core_claim": parsed["core_claim"],
                                        "search_queries": parsed["search_queries"][:3],
                                    }
                    elif response.status_code == 429:
                        continue
                except Exception as e:
                    logger.warning(f"Gemini claim extraction error on {model_name}: {e}")
                    continue

        return cls._fallback_extraction(cleaned_input)

    @classmethod
    def _fallback_extraction(cls, text: str) -> Dict[str, Any]:
        """Simple rule-based fallback when LLM is unavailable."""
        # Strip common viral prefixes
        clean = re.sub(
            r"^(forwarded as received|breaking news|viral message|attention|urgent|fake alert)[:\s\-]*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        first_sentence = clean.split("\n")[0].split(".")[0].strip()
        if not first_sentence:
            first_sentence = clean[:120]

        return {
            "core_claim": first_sentence,
            "search_queries": [
                f"{first_sentence[:80]} fact check",
                f"{first_sentence[:80]} news",
            ],
        }
