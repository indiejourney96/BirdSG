"""
bird_gate.py — First-pass filter: "Is this image a bird at all?"
"""

from app.species_mapping import get_species

BIRD_CONFIDENCE_THRESHOLD = 0.10


def passes_bird_gate(label: str, confidence: float) -> bool:
    species = get_species(label)

    return (
        species is not None
        and confidence >= BIRD_CONFIDENCE_THRESHOLD
    )