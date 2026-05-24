"""
bird_photos.py (v2) — Hybrid photo retrieval with local storage priority.

Strategy (optimized for post-MVP):
1. Try Supabase Storage (local, 50ms)
2. Fall back to Wikimedia Commons (200ms)
3. Return None gracefully

Use this AFTER you've run batch_download_bird_photos.py
For initial MVP, use the original bird_photos.py (Wikimedia only)
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=500)
def get_bird_photo(ebird_code: str, common_name: str) -> dict | None:
    """
    Fetch bird photo with local storage priority.

    Strategy:
    1. Try Supabase Storage first (fast, already cached)
    2. Fall back to Wikimedia Commons (slower but reliable)
    3. Return None gracefully if neither has photo

    Args:
        ebird_code: eBird code, e.g. "asikoe2"
        common_name: Common name, e.g. "Asian Koel"

    Returns:
        {
          "url": "https://...",
          "source": "Supabase Storage" | "Wikimedia Commons"
        }
        or None if no photo found.
    """
    
    # Try Supabase Storage first (local, fast ~50ms)
    photo = _get_supabase_photo(ebird_code)
    if photo:
        logger.debug("Photo found in Supabase Storage for %s", ebird_code)
        return photo
    
    # Fall back to Wikimedia (slower ~200ms but graceful)
    photo = _get_wikimedia_photo(common_name)
    if photo:
        logger.debug("Photo found via Wikimedia for %s", common_name)
        return photo
    
    # No photo found
    logger.debug("No photo found for %s", common_name)
    return None


def _get_supabase_photo(ebird_code: str) -> dict | None:
    """Fetch from Supabase Storage (local)."""
    try:
        from app.supabase_storage import get_photo_from_storage
        
        photo = get_photo_from_storage(ebird_code)
        return photo
    
    except Exception as exc:
        logger.debug("Supabase photo fetch failed for %s: %s", ebird_code, exc)
        return None


def _get_wikimedia_photo(species_name: str) -> dict | None:
    """Fetch from Wikimedia Commons (fallback)."""
    try:
        from app.wikimedia import get_wikimedia_photo
        
        photo = get_wikimedia_photo(species_name)
        return photo
    
    except Exception as exc:
        logger.debug("Wikimedia photo fetch failed for %s: %s", species_name, exc)
        return None
