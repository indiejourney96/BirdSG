"""
bird_gate.py — First-pass filter: "Is this image a bird at all?"
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Genuine bird classes from ImageNet-1k
# Used only for bird-vs-nonbird gating.
# ---------------------------------------------------------------------------
IMAGENET_BIRD_CLASSES: frozenset[str] = frozenset({
    # Passerines
    "brambling",
    "bulbul",
    "chickadee",
    "goldfinch",
    "house finch",
    "indigo bunting",
    "jay",
    "junco",
    "magpie",
    "robin",
    "starling",
    "water ouzel",
    "wren",
    "yellow-headed blackbird",

    # Raptors
    "bald eagle",
    "kite",
    "vulture",

    # Waders & shorebirds
    "american egret",
    "bittern",
    "crane",
    "dowitcher",
    "european gallinule",
    "flamingo",
    "limpkin",
    "little blue heron",
    "oystercatcher",
    "red-backed sandpiper",
    "redshank",
    "ruddy turnstone",
    "spoonbill",

    # Seabirds
    "albatross",
    "black-footed albatross",
    "black stork",
    "frigatebird",
    "king penguin",
    "pelican",
    "white stork",

    # Tropical / exotic
    "bee eater",
    "coucal",
    "hornbill",
    "hummingbird",
    "jacamar",
    "lorikeet",
    "motmot",
    "sunbird",
    "toucan",

    # Waterfowl & game birds
    "black grouse",
    "black swan",
    "bustard",
    "drake",
    "goose",
    "grouse",
    "partridge",
    "peacock",
    "prairie chicken",
    "ptarmigan",
    "quail",
    "red-breasted merganser",
    "ruffed grouse",

    # Other
    "ostrich",
    "pigeon",
})

# Minimum confidence required before trusting prediction
BIRD_CONFIDENCE_THRESHOLD = 0.10


def passes_bird_gate(label: str, confidence: float) -> bool:
    """
    Return True only if the model is reasonably confident
    the uploaded image contains a bird.

    This function DOES NOT check:
    - Singapore species validity
    - custom dataset membership
    - eBird taxonomy

    It ONLY checks:
    1. Is the predicted class bird-related?
    2. Is confidence high enough?
    """

    normalised = label.lower().strip()

    label_is_bird = (
        normalised in IMAGENET_BIRD_CLASSES
        or any(
            bird in normalised or normalised in bird
            for bird in IMAGENET_BIRD_CLASSES
        )
    )

    return (
        label_is_bird
        and confidence >= BIRD_CONFIDENCE_THRESHOLD
    )