"""
database.py — Supabase client and sighting persistence.

Required env vars (.env for local, dashboard for production):
    SUPABASE_URL  — https://your-project-ref.supabase.co
    SUPABASE_KEY  — service_role key (Dashboard → Settings → API)
"""

from __future__ import annotations

import logging
import os

from supabase import Client, create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

TABLE = "sightings"


def _init_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials. "
            "Check SUPABASE_URL and SUPABASE_KEY."
        )

    return create_client(url, key)


supabase: Client = _init_client()


def save_sighting(
    filename: str,
    predictions: list[dict],
    singapore_filtered: bool,
    image_url: str | None = None,
) -> dict:
    """Insert a sighting and return the created row (includes id and created_at)."""
    row = {
        "filename":           filename,
        "image_url":          image_url,
        "predictions":        predictions,
        "singapore_filtered": singapore_filtered,
    }
    response = supabase.table(TABLE).insert(row).execute()
    return response.data[0]