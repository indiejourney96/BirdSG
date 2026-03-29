"""
ebird.py — eBird API client for species info and recent Singapore sightings.

API docs: https://documenter.getpostman.com/view/664302/S1ENwy59
Base URL: https://api.ebird.org/v2

Two endpoints used:
    /ref/taxonomy/ebird?species={code}   — species name, family, order
    /data/obs/SG/recent/{code}           — recent sightings in Singapore

Results are cached in memory for 1 hour to avoid hammering the API
on repeated lookups of the same species.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

EBIRD_BASE     = "https://api.ebird.org/v2"
EBIRD_REGION   = "SG"
CACHE_TTL_SECS = 3600   # 1 hour

# Simple in-memory cache: key → (timestamp, data)
_cache: dict[str, tuple[float, Any]] = {}


def _get_api_key() -> str:
    key = os.environ.get("EBIRD_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Missing EBIRD_API_KEY. Add it to your .env file."
        )
    return key


def _cached(key: str) -> Any | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL_SECS:
            return data
    return None


def _store(key: str, data: Any) -> None:
    _cache[key] = (time.time(), data)


def get_species_info(species_code: str) -> dict | None:
    """
    Fetch species taxonomy info from eBird.
    Returns: {common_name, scientific_name, family, order} or None on failure.
    """
    cache_key = f"taxonomy:{species_code}"
    if cached := _cached(cache_key):
        return cached

    try:
        resp = httpx.get(
            f"{EBIRD_BASE}/ref/taxonomy/ebird",
            params={"species": species_code, "fmt": "json"},
            headers={"X-eBirdApiToken": _get_api_key()},
            timeout=5,
        )
        resp.raise_for_status()
        taxa = resp.json()

        if not taxa:
            return None

        t = taxa[0]
        result = {
            "common_name":     t.get("comName"),
            "scientific_name": t.get("sciName"),
            "family":          t.get("familyComName"),
            "order":           t.get("order"),
        }
        _store(cache_key, result)
        return result

    except Exception as exc:
        logger.error("eBird taxonomy fetch failed for %s: %s", species_code, exc)
        return None


def get_recent_sightings(species_code: str, max_results: int = 5) -> list[dict]:
    """
    Fetch recent Singapore sightings for a species from eBird.
    Returns list of {location, date, count}.
    """
    cache_key = f"sightings:{species_code}"
    if cached := _cached(cache_key):
        return cached

    try:
        resp = httpx.get(
            f"{EBIRD_BASE}/data/obs/{EBIRD_REGION}/recent/{species_code}",
            params={"maxResults": max_results, "back": 14},  # last 14 days
            headers={"X-eBirdApiToken": _get_api_key()},
            timeout=5,
        )
        resp.raise_for_status()

        results = [
            {
                "location": obs.get("locName"),
                "date":     obs.get("obsDt"),
                "count":    obs.get("howMany"),
            }
            for obs in resp.json()
        ]
        _store(cache_key, results)
        return results

    except Exception as exc:
        logger.error("eBird sightings fetch failed for %s: %s", species_code, exc)
        return []