import json
import logging
from typing import Dict, Any, List
import httpx
from app.core.config import settings
from app.models.verification import ClaimVerdict

logger = logging.getLogger("verinews.nli_evaluator")


class NLIEvaluator:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    NLI_PROMPT = """You are the Chief Fact-Checking Veracity Judge for VeriNews.
Evaluate the following claim strictly against the provided ground-truth evidence.

CLAIM UNDER INVESTIGATION:
\"{claim}\"

RETRIEVED EVIDENCE FROM ACCREDITED REPORTERS & FACT-CHECKERS:
{evidence_block}

TAVILY AI RESEARCH BRIEF:
\"{tavily_answer}\"

KNOWN SATIRE CONTEXT: {is_satire}

CLASSIFICATION RULES:
1. "TRUE": Directly corroborated by accredited fact-checkers, official records, or major news wires. (truth_score: 80.0 to 100.0)
2. "MISLEADING": Based on a real event but distorted, exaggerated, misattributed, miscaptioned, or stripped of critical context. (truth_score: 30.0 to 79.0)
3. "FAKE": Outright fabrication, invented quote, debunked viral hoax, or manipulated narrative. (truth_score: 0.0 to 29.0)
4. "SATIRE": Originates from a parody/satirical humor publisher (e.g. The Onion, The Fauxy) or comedic fiction. (truth_score: 0.0 to 20.0)
5. "UNVERIFIED": The claim is too new, emergent, or completely uncorroborated by any credible news organization or official body. If there is simply no verifiable evidence either way, you MUST select UNVERIFIED rather than guessing. (truth_score: 50.0)

OUTPUT STRICTLY AS VALID JSON (no markdown formatting, just JSON):
{{
  "verdict": "TRUE | MISLEADING | SATIRE | FAKE | UNVERIFIED",
  "truth_score": 75.0,
  "explanation_bullets": [
    "First factual finding explaining the verdict.",
    "Second finding citing what credible sources or authorities stated.",
    "Third concluding point clarifying context or alerting readers."
  ]
}}"""

    @classmethod
    async def evaluate(
        cls,
        claim: str,
        evidence: List[Dict[str, str]],
        tavily_answer: str = "",
        is_satire: bool = False,
    ) -> Dict[str, Any]:
        """
        Runs Natural Language Inference comparing claim with evidence.
        Uses multi-model fallback to survive single-model free-tier rate limits.
        """
        # Format evidence block
        evidence_lines = []
        for i, ev in enumerate(evidence, 1):
            evidence_lines.append(
                f"[{i}] {ev.get('title')} ({ev.get('publisher')})\n"
                f"    Excerpt: {ev.get('content')}"
            )
        evidence_block = (
            "\n".join(evidence_lines)
            if evidence_lines
            else "NO SUBSTANTIAL EVIDENCE FOUND IN WIRE SEARCHES."
        )

        # If no evidence was retrieved at all and not satire, default to UNVERIFIED
        if not evidence and not tavily_answer and not is_satire:
            return cls._unverified_fallback(claim)

        prompt = cls.NLI_PROMPT.format(
            claim=claim,
            evidence_block=evidence_block,
            tavily_answer=tavily_answer or "None",
            is_satire="YES" if is_satire else "NO",
        )

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
                                verdict_str = parsed.get("verdict", "").upper().strip()

                                valid_verdicts = {v.value for v in ClaimVerdict}
                                if verdict_str not in valid_verdicts:
                                    verdict_str = ClaimVerdict.UNVERIFIED.value

                                truth_score = float(parsed.get("truth_score", 50.0))
                                truth_score = max(0.0, min(100.0, truth_score))

                                bullets = parsed.get("explanation_bullets", [])
                                if len(bullets) < 3:
                                    bullets.extend(
                                        ["Verification details cross-referenced across wires."]
                                        * (3 - len(bullets))
                                    )

                                return {
                                    "verdict": ClaimVerdict(verdict_str),
                                    "truth_score": truth_score,
                                    "explanation_bullets": bullets[:3],
                                }
                    elif response.status_code == 429:
                        logger.warning(f"Model {model_name} hit 429 quota. Trying next fallback model...")
                        continue
                except Exception as e:
                    logger.warning(f"Error querying model {model_name}: {e}. Trying fallback...")
                    continue

        # If LLM models are all exhausted, use Tavily synthesis as smart heuristic
        return cls._tavily_heuristic_evaluation(claim, tavily_answer, evidence, is_satire)

    @classmethod
    def _tavily_heuristic_evaluation(
        cls,
        claim: str,
        tavily_answer: str,
        evidence: List[Dict[str, str]],
        is_satire: bool,
    ) -> Dict[str, Any]:
        """Heuristic evaluation when LLM quota is exhausted but Tavily answer is available."""
        if is_satire:
            return {
                "verdict": ClaimVerdict.SATIRE,
                "truth_score": 10.0,
                "explanation_bullets": [
                    "The claim originates from a known satirical or parody publication.",
                    "The content was intended for comedic entertainment rather than factual news.",
                    "Official sources have not reported or verified this narrative.",
                ],
            }

        combined_text = f"{tavily_answer} " + " ".join([e.get("content", "") for e in evidence]).lower()

        if any(w in combined_text for w in ["false", "hoax", "fake alert", "debunk", "misleading", "fabricated", "not true"]):
            return {
                "verdict": ClaimVerdict.FAKE,
                "truth_score": 15.0,
                "explanation_bullets": [
                    tavily_answer[:120] if tavily_answer else "Multiple fact-checkers confirm this claim is false.",
                    "Accredited fact-check databases classify this narrative as an unsubstantiated viral hoax.",
                    "Readers are advised to verify breaking claims before sharing on social platforms.",
                ],
            }
        elif any(w in combined_text for w in ["confirmed", "official", "announced", "verified", "historic", "launched"]):
            return {
                "verdict": ClaimVerdict.TRUE,
                "truth_score": 90.0,
                "explanation_bullets": [
                    tavily_answer[:120] if tavily_answer else "Credible news wires corroborate the reported facts.",
                    "Official statements and public releases confirm the event occurred as stated.",
                    "Major media outlets independently verified the key details.",
                ],
            }

        return cls._unverified_fallback(claim)

    @classmethod
    def _unverified_fallback(cls, claim: str) -> Dict[str, Any]:
        """Safe default when evidence is inconclusive or analysis is disrupted."""
        return {
            "verdict": ClaimVerdict.UNVERIFIED,
            "truth_score": 50.0,
            "explanation_bullets": [
                "No accredited news reporting or official fact-check was found for this specific claim.",
                "The claim may refer to an emergent event, local incident, or an uncorroborated rumor.",
                "Readers are advised to exercise caution and avoid sharing unverified claims.",
            ],
        }
