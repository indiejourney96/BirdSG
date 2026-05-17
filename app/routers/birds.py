"""
birds.py — GET /birds/{label} endpoint.

Accepts an ImageNet label (e.g. "bulbul") and returns:
  - The mapped Singapore species info from eBird taxonomy
  - Recent sightings in Singapore from eBird observations
  - A Xeno-canto reference recording for the species
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ebird import get_recent_sightings, get_species_info
from app.species_mapping import get_species
from app.xeno_canto import get_reference_audio

router = APIRouter(prefix="/birds", tags=["birds"])


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


class BirdInfoResponse(BaseModel):
    label: str
    ebird_code: str
    species: SpeciesInfo
    recent_sightings_sg: list[RecentSighting]
    recording: RecordingInfo | None = None


@router.get("/{label}", response_model=BirdInfoResponse)
def get_bird_info(label: str):
    """
    Look up species info, recent Singapore sightings, and a reference
    recording for an ImageNet label.
    """
    species = get_species(label)

    ebird_code = species["ebird_code"]
    if ebird_code is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Singapore species mapping found for label '{label}'.",
        )

    species   = get_species_info(ebird_code)
    sightings = get_recent_sightings(ebird_code)

    if species is None:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve species info from eBird for '{label}'.",
        )

    # Fetch Xeno-canto recording using the resolved common name
    recording: RecordingInfo | None = None
    xc = get_reference_audio(species["scientific_name"])
    if xc:
        recording = RecordingInfo(**xc)

    return BirdInfoResponse(
        label=label,
        ebird_code=ebird_code,
        species=SpeciesInfo(**species),
        recent_sightings_sg=[RecentSighting(**s) for s in sightings],
        recording=recording,
    )