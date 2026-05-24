"""
birds.py — GET /birds/{label} endpoint with photos, species details, and recordings.

Returns:
  - eBird taxonomy (common name, scientific name, family, order)
  - Bird photo (from eBird or Wikimedia)
  - Recent Singapore sightings from eBird
  - Xeno-canto reference recording
  - Rich species details from Supabase
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ebird import get_recent_sightings, get_species_info
from app.species_mapping import get_species
from app.xeno_canto import get_reference_audio
from app.bird_photos import get_bird_photo
from app.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/birds", tags=["birds"])


# ─────────────────────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────────────────────

class SpeciesInfo(BaseModel):
    common_name: str | None
    scientific_name: str | None
    family: str | None
    order: str | None


class PhotoInfo(BaseModel):
    url: str
    caption: str | None = None
    photographer: str | None = None
    license: str | None = None
    source: str


class RecentSighting(BaseModel):
    location: str | None
    date: str | None
    count: int | None


class RecordingInfo(BaseModel):
    audio_url: str | None
    recording_id: str | None
    recordist: str | None
    location: str | None


class SpeciesDetails(BaseModel):
    general_knowledge: str | None = None
    identification_tips: str | None = None
    habitat: str | None = None
    behaviour: str | None = None
    diet: str | None = None
    feeding_habits: str | None = None


class BirdInfoResponse(BaseModel):
    label: str
    ebird_code: str
    species: SpeciesInfo
    photo: PhotoInfo | None = None
    recent_sightings_sg: list[RecentSighting]
    recording: RecordingInfo | None = None
    details: SpeciesDetails | None = None


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_bird_details_from_db(ebird_code: str) -> dict | None:
    """
    Fetch species details from bird_species_details table including photo urls.
    Returns None if not found or on DB error.
    """
    try:
        # ADDED photo_url AND photo_source TO THE SELECT STATEMENT
        response = supabase.table("bird_species_details").select(
            "general_knowledge, identification_tips, habitat, behaviour, diet, feeding_habits, photo_url, photo_source"
        ).eq("ebird_code", ebird_code).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    except Exception as exc:
        logger.error("Failed to fetch bird details for %s: %s", ebird_code, exc)
        return None

# ─────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────

@router.get("/{label}", response_model=BirdInfoResponse)
def get_bird_info(label: str):
    """
    Look up comprehensive bird info: taxonomy, photo, sightings, recording, and details.
    """
    species = get_species(label)

    ebird_code = species["ebird_code"] if species else None
    if ebird_code is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Singapore species mapping found for label '{label}'.",
        )

    # Fetch eBird taxonomy
    ebird_species = get_species_info(ebird_code)
    if ebird_species is None:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve species info from eBird for '{label}'.",
        )

    # 1. Fetch rich species details from Supabase first
    details: SpeciesDetails | None = None
    photo: PhotoInfo | None = None

    bird_details = get_bird_details_from_db(ebird_code)
    if bird_details:
        details = SpeciesDetails(**bird_details)
        
        # Check if the database record already holds a pre-saved photo URL
        if bird_details.get("photo_url"):
            photo = PhotoInfo(
                url=bird_details["photo_url"],
                source=bird_details.get("photo_source") or "Supabase Database",
                caption=f"An amazing {ebird_species['common_name']}"
            )

    # 2. Fallback: If DB table had no photo, use your hybrid storage/Wikimedia asset strategy
    if not photo:
        logger.info("Photo not found in DB table metadata. Running asset fallback strategy for %s", ebird_code)
        photo_data = get_bird_photo(ebird_code, ebird_species["common_name"])
        if photo_data:
            photo = PhotoInfo(**photo_data)

    # Fetch recent sightings (graceful: returns empty list)
    sightings = get_recent_sightings(ebird_code)

    # Fetch reference recording (graceful: returns None)
    recording: RecordingInfo | None = None
    xc = get_reference_audio(ebird_species["common_name"])
    if xc:
        recording = RecordingInfo(**xc)

    return BirdInfoResponse(
        label=label,
        ebird_code=ebird_code,
        species=SpeciesInfo(**ebird_species),
        photo=photo,
        recent_sightings_sg=[RecentSighting(**s) for s in sightings],
        recording=recording,
        details=details,
    )