"""
database.py — Supabase client and sighting persistence.

Required env vars (.env for local, dashboard for production):
    SUPABASE_URL  — https://your-project-ref.supabase.co
    SUPABASE_KEY  — service_role key (Dashboard → Settings → API)
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
import re
from pathlib import Path
from uuid import uuid4

from supabase import Client, create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

TABLE = "sightings"
BUCKET_NAME = "user-bird-sightings"
SIGNED_URL_EXPIRES_IN = 60 * 60

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _init_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials. "
            "Copy .env.example → .env and fill in SUPABASE_URL and SUPABASE_KEY."
        )

    return create_client(url, key)


supabase: Client = _init_client()


def _safe_filename(original_filename: str, content_type: str | None) -> str:
    path = Path(original_filename or "bird")
    stem = _SAFE_FILENAME_RE.sub("_", path.stem).strip("._-") or "bird"
    suffix = path.suffix.lower()

    if suffix not in _EXTENSION_BY_CONTENT_TYPE.values():
        suffix = _EXTENSION_BY_CONTENT_TYPE.get(content_type or "", ".jpg")

    return f"{stem}{suffix}"


def build_sighting_storage_path(
    original_filename: str,
    content_type: str | None = None,
) -> tuple[str, str, str]:
    """Return the storage folder, saved filename, and full object key."""
    now = datetime.now(timezone.utc)
    storage_path = f"sightings/{now:%Y/%m/%d}/{uuid4().hex}"
    filename = _safe_filename(original_filename, content_type)
    object_path = f"{storage_path}/{filename}"
    return storage_path, filename, object_path


def upload_sighting_image(
    object_path: str,
    image_bytes: bytes,
    content_type: str | None,
) -> str:
    """Upload a sighting image to the private Storage bucket."""
    options = {
        "content-type": content_type or "application/octet-stream",
        "upsert": "false",
    }
    supabase.storage.from_(BUCKET_NAME).upload(
        path=object_path,
        file=image_bytes,
        file_options=options,
    )
    return object_path


def create_sighting_image_url(object_path: str, expires_in: int = SIGNED_URL_EXPIRES_IN) -> str | None:
    """Create a signed URL for a private sighting image."""
    response = supabase.storage.from_(BUCKET_NAME).create_signed_url(object_path, expires_in)

    data = getattr(response, "data", response)

    if isinstance(data, dict):
        return (
            data.get("signedURL")
            # or data.get("signedUrl")
            # or data.get("signed_url")
        )

    return None


def save_sighting(
    filename: str,
    storage_path: str,
    predictions: list[dict],
    singapore_filtered: bool,
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    """Insert a sighting and return the created row (includes id and created_at)."""
    row = {
        "filename":           filename,
        "storage_path":       storage_path,
        "predictions":        predictions,
        "singapore_filtered": singapore_filtered,
        "lat":                lat,
        "lng":                lng,
    }
    response = supabase.table(TABLE).insert(row).execute()
    return response.data[0]
