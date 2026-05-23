"""
birds.py — GET /birds/{label} endpoint with rich species details.

Returns:
  - eBird taxonomy (common name, scientific name, family, order)
  - Recent Singapore sightings from eBird
  - Xeno-canto reference recording
  - Rich species details from Supabase (knowledge, ID tips, habitat, behaviour, diet)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ebird import get_recent_sightings, get_species_info
from app.species_mapping import get_species
from app.xeno_canto import get_reference_audio
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
    recent_sightings_sg: list[RecentSighting]
    recording: RecordingInfo | None = None
    details: SpeciesDetails | None = None


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_bird_details_from_db(ebird_code: str) -> dict | None:
    """
    Fetch species details from bird_species_details table.
    Returns None if not found or on DB error (graceful failure).
    """
    try:
        response = supabase.table("bird_species_details").select(
            "general_knowledge, identification_tips, habitat, behaviour, diet, feeding_habits"
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
    Look up species info, recent Singapore sightings, reference recording,
    and rich details for an ImageNet label.
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

    # Fetch recent sightings (graceful failure: returns empty list)
    sightings = get_recent_sightings(ebird_code)

    # Fetch reference recording (graceful failure: returns None)
    recording: RecordingInfo | None = None
    xc = get_reference_audio(ebird_species["common_name"])
    if xc:
        recording = RecordingInfo(**xc)

    # Fetch rich species details from Supabase (graceful failure: returns None)
    details: SpeciesDetails | None = None
    bird_details = get_bird_details_from_db(ebird_code)
    if bird_details:
        details = SpeciesDetails(**bird_details)

    return BirdInfoResponse(
        label=label,
        ebird_code=ebird_code,
        species=SpeciesInfo(**ebird_species),
        recent_sightings_sg=[RecentSighting(**s) for s in sightings],
        recording=recording,
        details=details,
    )