import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx
from duckduckgo_search import DDGS
from app.core.config import settings

logger = logging.getLogger("verinews.evidence_retriever")

SATIRE_DOMAINS = [
    "theonion.com",
    "thefauxy.com",
    "fakingnews.com",
    "babylonbee.com",
    "newsthump.com",
    "satirewire.com",
]


class EvidenceRetriever:
    @classmethod
    async def retrieve_evidence(
        cls,
        queries: List[str],
        submitted_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves real-time evidence using Tavily with automatic DDGS fallback,
        and evaluates domain satire classification.
        """
        is_satire = False
        evidence_items: List[Dict[str, str]] = []
        tavily_ai_answer = ""

        # 1. Satire Domain Inspection
        if submitted_url:
            domain = urlparse(submitted_url).netloc.lower()
            if any(s in domain for s in SATIRE_DOMAINS):
                is_satire = True

        for query in queries:
            if any(s in query.lower() for s in SATIRE_DOMAINS):
                is_satire = True

        # 2. Query Tavily Search API if key is present
        if settings.TAVILY_API_KEY:
            primary_query = queries[0] if queries else ""
            tavily_results = await cls._query_tavily(primary_query)
            if tavily_results.get("results"):
                evidence_items.extend(tavily_results["results"])
                tavily_ai_answer = tavily_results.get("answer", "")

        # 3. Fallback or augment with DuckDuckGo Search (DDGS)
        if len(evidence_items) < 2 and queries:
            ddg_query = queries[0]
            ddg_results = cls._query_ddgs(ddg_query, max_results=3)
            # Add non-duplicate URLs
            existing_urls = {item["url"] for item in evidence_items}
            for item in ddg_results:
                if item["url"] not in existing_urls:
                    evidence_items.append(item)
                    existing_urls.add(item["url"])

        return {
            "evidence": evidence_items[:5],
            "tavily_answer": tavily_ai_answer,
            "is_satire": is_satire,
        }

    @classmethod
    async def _query_tavily(cls, query: str) -> Dict[str, Any]:
        """Queries Tavily Search API for AI-curated search results and summary answer."""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 4,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "")
                    results = []
                    for r in data.get("results", []):
                        domain = urlparse(r.get("url", "")).netloc.replace("www.", "")
                        results.append(
                            {
                                "title": r.get("title", "News Wire Report"),
                                "url": r.get("url", ""),
                                "content": r.get("content", "")[:350],
                                "publisher": domain or "Verified News Outlet",
                            }
                        )
                    return {"results": results, "answer": answer}
        except Exception as e:
            logger.warning(f"Tavily search query failed: {e}")

        return {"results": [], "answer": ""}

    @classmethod
    def _query_ddgs(cls, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Queries DuckDuckGo search as a reliable, zero-cost fallback."""
        results = []
        try:
            with DDGS() as ddgs:
                ddg_res = list(ddgs.text(query, max_results=max_results))
                for r in ddg_res:
                    domain = urlparse(r.get("href", "")).netloc.replace("www.", "")
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "content": r.get("body", "")[:350],
                            "publisher": domain or "Web Source",
                        }
                    )
        except Exception as e:
            logger.error(f"DDGS search query failed: {e}")

        return results
