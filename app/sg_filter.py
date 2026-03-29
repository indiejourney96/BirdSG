"""
sg_filter.py — Second-pass filter: "Is this bird found in Singapore?"

This module answers ONE question after bird_gate.py has confirmed we're
looking at a bird:
    "Does this ImageNet label correspond to a species recorded in Singapore?"

HOW IT WORKS
------------
ImageNet uses short generic names ("bulbul", "kingfisher") while Singapore
species lists use full IOC names ("Yellow-vented Bulbul", "Collared Kingfisher").

We use substring matching in both directions:
  - Does any SG species name CONTAIN the model label?  (label="kingfisher" → "Collared Kingfisher" ✓)
  - Does the model label CONTAIN a key SG species word? (rarely needed, but handles edge cases)

WHAT THIS MODULE IS NOT
-----------------------
This filter only keeps or drops predictions. It does NOT look up species info
or fetch eBird sightings — that's ebird.py's job.
"""

from app.sg_species import _SG_SPECIES_LOWER


def is_singapore_species(label: str) -> bool:
    """
    Return True if the model label plausibly matches a Singapore bird species.

    Matching is deliberately generous (substring both ways) because ImageNet
    labels are generic: "kingfisher" should match "Collared Kingfisher",
    "Common Kingfisher", etc.

    Example matches:
        "bulbul"      → "Yellow-vented Bulbul"          ✓
        "kingfisher"  → "Collared Kingfisher"            ✓
        "kite"        → "Brahminy Kite", "Black Kite"    ✓
        "bald eagle"  → (no SG species contains this)    ✗
    """
    normalised = label.lower().strip()

    # Exact match first (fast path)
    if normalised in _SG_SPECIES_LOWER:
        return True

    # Substring match — label word found inside a SG species name, or vice versa
    return any(
        normalised in sg_name or sg_name in normalised
        for sg_name in _SG_SPECIES_LOWER
    )
