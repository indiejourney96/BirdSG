"""
wikimedia.py — Fetch bird photos from Wikimedia Commons API.

Free, CC-licensed, no API key required.
Hit rate: ~82% for Singapore birds.

The key fix: Use browser-like headers and User-Agent to avoid 403 Forbidden.
API works fine when headers match what a real browser sends.

API docs: https://commons.wikimedia.org/wiki/Commons:API
"""

import logging
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
TIMEOUT = 10


@lru_cache(maxsize=500)
def get_wikimedia_photo(species_name: str) -> dict | None:
    """
    Fetch bird photo from Wikimedia Commons.

    Args:
        species_name: Common name, e.g. "Asian Koel"

    Returns:
        {
          "url": "https://upload.wikimedia.org/...",
          "title": "File:Species name.jpg",
          "source": "Wikimedia Commons"
        }
        or None if not found / error.
    """
    try:
        # Browser-like headers to avoid 403 Forbidden
        # Compliant headers matching Wikimedia's User-Agent policy
        headers = {
        "User-Agent": "BirdSGApp/1.0 (daryl@hotmail.com) httpx/0.27.0",
        "Accept": "application/json"
        }

        # Step 1: Search for species in File namespace
        logger.debug("Searching Wikimedia for: %s", species_name)
        resp = httpx.get(
            COMMONS_API,
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{species_name} bird",
                "srnamespace": 6,  # File namespace only
                "srlimit": 1,
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            logger.debug("No Wikimedia photo found for: %s", species_name)
            return None

        file_title = search_results[0]["title"]
        logger.debug("Found Wikimedia file: %s", file_title)

        # Step 2: Get file details (URL, license, etc.)
        resp = httpx.get(
            COMMONS_API,
            params={
                "action": "query",
                "titles": file_title,
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
            },
            headers=headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = list(pages.values())[0]
        image_info = page.get("imageinfo", [{}])[0]

        photo_url = image_info.get("url")
        if not photo_url:
            return None

        return {
            "url": photo_url,
            "title": file_title,
            "source": "Wikimedia Commons",
        }

    except httpx.TimeoutException:
        logger.warning("Wikimedia timeout for: %s", species_name)
        return None
    except httpx.HTTPStatusError as e:
        logger.error("Wikimedia HTTP error for %s: %s %s", species_name, e.response.status_code, e.response.text[:200])
        return None
    except Exception as exc:
        logger.error("Wikimedia fetch failed for %s: %s", species_name, exc)
        return None