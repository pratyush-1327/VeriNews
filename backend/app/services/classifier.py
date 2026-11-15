import re
from typing import Tuple, Optional
from app.models.source import NewsScope, Source


class CityClassifier:
    CITY_PATTERNS = {
        "delhi": [
            r"\bdelhi\b",
            r"\bnew delhi\b",
            r"\bncr\b",
            r"\bnoida\b",
            r"\bgurugram\b",
            r"\bgurgaon\b",
            r"\byamuna\b",
            r"\bconnaught place\b",
        ],
        "jaipur": [
            r"\bjaipur\b",
            r"\bpink city\b",
            r"\brajasthan\b",
            r"\bhawa mahal\b",
            r"\bamer\b",
        ],
        "mumbai": [
            r"\bmumbai\b",
            r"\bbombay\b",
            r"\bthane\b",
            r"\bbkc\b",
            r"\bbandra\b",
            r"\bnavi mumbai\b",
            r"\bmarine drive\b",
        ],
        "bengaluru": [
            r"\bbengaluru\b",
            r"\bbangalore\b",
            r"\bwhitefield\b",
            r"\bkoramangala\b",
            r"\bindiranagar\b",
            r"\bkempegowda\b",
            r"\belectronic city\b",
        ],
        "chennai": [
            r"\bchennai\b",
            r"\bmadras\b",
            r"\bmarina beach\b",
            r"\banna nagar\b",
            r"\badyar\b",
            r"\btamil nadu\b",
        ],
        "kolkata": [
            r"\bkolkata\b",
            r"\bcalcutta\b",
            r"\bhowrah\b",
            r"\bsalt lake\b",
            r"\bpark street\b",
            r"\bwest bengal\b",
        ],
    }

    @classmethod
    def classify(
        cls,
        title: str,
        text: str,
        source: Source,
    ) -> Tuple[NewsScope, Optional[str]]:
        """
        Determines the appropriate NewsScope and city_tag for an article.
        """
        # If source is explicitly dedicated to a city, respect it
        if source.default_scope == NewsScope.CITY and source.default_city_tag:
            return NewsScope.CITY, source.default_city_tag.lower()

        # If source is global, keep as global unless strongly city-specific
        if source.default_scope == NewsScope.GLOBAL:
            return NewsScope.GLOBAL, None

        # Check title and first 1000 characters for city mentions
        search_corpus = f"{title} {text[:1000]}".lower()

        # Priority 1: Check title first (strongest indicator)
        title_lower = title.lower()
        for city, patterns in cls.CITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, title_lower):
                    return NewsScope.CITY, city

        # Priority 2: Check body text
        for city, patterns in cls.CITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, search_corpus):
                    return NewsScope.CITY, city

        # Fallback to source's default scope
        return source.default_scope, source.default_city_tag
