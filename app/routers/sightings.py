"""
sightings.py — GET /sightings/{id} endpoint.

Allows a user to retrieve a specific sighting by its Supabase UUID,
returned to them as sighting_id in the /predict response.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import (
    SIGNED_URL_EXPIRES_IN,
    TABLE,
    create_sighting_image_url,
    supabase,
)

router = APIRouter(prefix="/sightings", tags=["sightings"])


class SightingResponse(BaseModel):
    id: str
    filename: str
    storage_path: str
    image_url: str | None
    predictions: list[dict]
    singapore_filtered: bool
    created_at: str
    lat: float | None
    lng: float | None


@router.get("/{sighting_id}", response_model=SightingResponse)
def get_sighting(sighting_id: UUID):
    """Retrieve a single sighting by its UUID."""
    response = (
        supabase.table(TABLE)
        .select("id, filename, storage_path, predictions, singapore_filtered, created_at, lat, lng")
        .eq("id", str(sighting_id))
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Sighting {sighting_id} not found.")

    data = dict(response.data)
    storage_path = data.get("storage_path")
    filename = data.get("filename")

    if storage_path and filename:
        object_path = f"{storage_path}/{filename}"
        data["image_url"] = create_sighting_image_url(object_path, SIGNED_URL_EXPIRES_IN)
    else:
        data["image_url"] = None

    return data
