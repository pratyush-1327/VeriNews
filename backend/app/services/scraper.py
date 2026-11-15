import re
import logging
from typing import Dict, Any, Optional
import httpx
import trafilatura
from app.core.config import settings
from app.core.ssrf import validate_url_ssrf

logger = logging.getLogger("verinews.scraper")


class ScraperService:
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @classmethod
    async def fetch_and_extract(
        cls,
        url: str,
        fallback_title: str = "",
        fallback_summary: str = "",
    ) -> Dict[str, Any]:
        """
        Fetches web page HTML and extracts clean text using trafilatura along with top image.
        Protected by SSRF guardrails and maximum payload limits.
        """
        # Enforce SSRF validation
        safe_url = await validate_url_ssrf(url)

        html_content = ""
        extracted_text = ""
        image_url: Optional[str] = None

        try:
            async with httpx.AsyncClient(
                headers=cls.HEADERS,
                timeout=8.0,
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                # Custom hook to validate redirects against SSRF
                async def response_hook(response: httpx.Response):
                    if response.is_redirect:
                        next_url = response.headers.get("Location")
                        if next_url:
                            # Re-validate target URL
                            resolved_next = response.url.join(next_url)
                            await validate_url_ssrf(str(resolved_next))

                client.event_hooks["response"] = [response_hook]

                resp = await client.get(safe_url)
                if resp.status_code == 200:
                    # Enforce max content length to protect against memory exhaustion
                    content_bytes = resp.content[: settings.MAX_SCRAPE_BYTES]
                    html_content = content_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Failed to fetch HTML for {url}: {e}")
            # If it's an SSRF HTTPException, let it propagate so API caller gets a clean 400
            from fastapi import HTTPException
            if isinstance(e, HTTPException):
                raise e

        if html_content:
            # 1. Extract clean text body via trafilatura
            try:
                extracted_text = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                ) or ""
            except Exception as e:
                logger.error(f"Trafilatura extraction error on {url}: {e}")

            # 2. Extract preview image from meta tags
            image_url = cls._extract_meta_image(html_content)

        # Use fallback if extraction was empty
        if not extracted_text or len(extracted_text.strip()) < 50:
            extracted_text = fallback_summary or fallback_title

        return {
            "text": extracted_text.strip(),
            "image_url": image_url,
        }

    @classmethod
    def _extract_meta_image(cls, html: str) -> Optional[str]:
        """Extracts OpenGraph or Twitter preview image from HTML."""
        # Try og:image
        og_match = re.search(
            r'<meta\s+[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if not og_match:
            og_match = re.search(
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
                html,
                re.IGNORECASE,
            )

        if og_match:
            return og_match.group(1).strip()

        # Try twitter:image
        tw_match = re.search(
            r'<meta\s+[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if tw_match:
            return tw_match.group(1).strip()

        return None
