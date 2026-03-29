"""
birds.py — GET /birds/{label} endpoint.

Accepts an ImageNet label (e.g. "bulbul") and returns:
  - The mapped Singapore species info from eBird taxonomy
  - Recent sightings in Singapore from eBird observations
  - The label → species mapping used, for transparency
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ebird import get_recent_sightings, get_species_info
from app.label_map import get_ebird_code

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


class BirdInfoResponse(BaseModel):
    label: str
    ebird_code: str
    species: SpeciesInfo
    recent_sightings_sg: list[RecentSighting]


@router.get("/{label}", response_model=BirdInfoResponse)
def get_bird_info(label: str):
    """
    Look up species info and recent Singapore sightings for an ImageNet label.
    """
    # Map label → eBird code
    ebird_code = get_ebird_code(label)

    if ebird_code is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Singapore species mapping found for label '{label}'.",
        )

    # Fetch from eBird (both calls use in-memory cache after first hit)
    species  = get_species_info(ebird_code)
    sightings = get_recent_sightings(ebird_code)

    if species is None:
        raise HTTPException(
            status_code=502,
            detail=f"Could not retrieve species info from eBird for '{label}'.",
        )

    return BirdInfoResponse(
        label=label,
        ebird_code=ebird_code,
        species=SpeciesInfo(**species),
        recent_sightings_sg=[RecentSighting(**s) for s in sightings],
    )