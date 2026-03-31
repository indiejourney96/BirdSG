"""
xeno_canto.py — Xeno-canto API v3 client for reference bird recordings.

API docs: https://xeno-canto.org/explore/api
Base URL: https://xeno-canto.org/api/3/recordings
Requires API key — obtain at: https://xeno-canto.org/account (free for registered members)

Add to .env:
    XENO_CANTO_API_KEY=your-key-here

Fetches the best available reference recording for a species,
preferring Singapore recordings of quality A or B where available.
Results cached in memory for 1 hour.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

XENO_CANTO_BASE = "https://xeno-canto.org/api/3/recordings"
CACHE_TTL_SECS  = 3600
SG_COUNTRY      = "Singapore"

_cache: dict[str, tuple[float, Any]] = {}


def _get_api_key() -> str:
    key = os.environ.get("XENO_CANTO_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "Missing XENO_CANTO_API_KEY. "
            "Register at xeno-canto.org and add the key to your .env file."
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


def _pick_best(recordings: list[dict]) -> dict | None:
    """
    Pick the best recording from a list.
    Priority:
      1. Singapore recording with quality A or B
      2. Any Singapore recording
      3. Any quality A recording
      4. First available
    """
    if not recordings:
        return None

    sg    = [r for r in recordings if r.get("cnt") == SG_COUNTRY]
    sg_ab = [r for r in sg if r.get("q") in ("A", "B")]
    any_a = [r for r in recordings if r.get("q") == "A"]

    return (sg_ab or sg or any_a or recordings)[0]


def get_reference_audio(species_name: str) -> dict | None:
    """
    Fetch the best reference recording for a species from Xeno-canto.

    Args:
        species_name: Common name e.g. "Yellow-vented Bulbul"

    Returns:
        {audio_url, recording_id, recordist, location} or None on failure.
    """
    cache_key = f"xc:{species_name.lower()}"
    if cached := _cached(cache_key):
        logger.info("Xeno-canto cache hit: %s", species_name)
        return cached

    try:
        normalized = species_name.replace("-", " ")
        query = f'en:"{normalized}" cnt:Singapore'
        logger.info("Xeno-canto query: %s", query)
        resp = httpx.get(
            XENO_CANTO_BASE,
            params={
                "query": f'en:"{normalized}" cnt:Singapore',
                "key":   _get_api_key(),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        recordings = data.get("recordings", [])
        best = _pick_best(recordings)

        if not best:
            return None

        result = {
            "audio_url":    f"{best.get('file')}",
            "recording_id": f"XC{best.get('id')}",
            "recordist":    best.get("rec"),
            "location":     best.get("loc"),
        }
        _store(cache_key, result)
        return result

    except Exception as exc:
        logger.error("Xeno-canto fetch failed for '%s': %s", species_name, exc)
        return None