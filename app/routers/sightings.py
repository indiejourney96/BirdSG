"""
sightings.py — GET /sightings/{id} endpoint.

Allows a user to retrieve a specific sighting by its Supabase UUID,
returned to them as sighting_id in the /predict response.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import supabase, TABLE

router = APIRouter(prefix="/sightings", tags=["sightings"])


class SightingResponse(BaseModel):
    id: str
    filename: str
    image_url: str | None
    predictions: list[dict]
    singapore_filtered: bool
    created_at: str


@router.get("/{sighting_id}", response_model=SightingResponse)
def get_sighting(sighting_id: UUID):
    """Retrieve a single sighting by its UUID."""
    response = (
        supabase.table(TABLE)
        .select("id, filename, image_url, predictions, singapore_filtered, created_at")
        .eq("id", str(sighting_id))
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Sighting {sighting_id} not found.")

    return response.data