"""
bird_gate.py — First-pass filter: "Is this image a bird at all?"

This module answers ONE question before any Singapore-specific logic runs:
    "Did the model see a bird, or was this a photo of a person, food, etc.?"

HOW IT WORKS
------------
EfficientNet-B0 is trained on ImageNet-1k (1000 classes). About 57 of those
classes are birds. If the model's top prediction is not in that 57-bird set,
or the confidence is too low to trust, we reject the image early with a clear
error message — saving unnecessary eBird lookups and DB writes.

WHAT THIS MODULE IS NOT
-----------------------
This is not the Singapore species filter. A photo of a bald eagle might pass
this gate (it's clearly a bird) but fail later in sg_filter.py because bald
eagles don't live in Singapore.

NOTE ON MISSING LABELS
----------------------
"kingfisher", "swallow", "swift", "sparrow", "warbler" are NOT ImageNet-1k
classes. The model will never predict these labels directly. They only appear
as matches in sg_filter.py via substring matching against Singapore species
names.
"""

# ---------------------------------------------------------------------------
# The ~57 genuine bird classes in ImageNet-1k.
# Sourced from WordNet synsets used by EfficientNet_B0_Weights.DEFAULT.
# ---------------------------------------------------------------------------
IMAGENET_BIRD_CLASSES: frozenset[str] = frozenset({
    # Passerines
    "brambling", "bulbul", "chickadee", "goldfinch", "house finch",
    "indigo bunting", "jay", "junco", "magpie", "robin", "starling",
    "water ouzel", "wren", "yellow-headed blackbird",
    # Raptors
    "bald eagle", "kite", "vulture",
    # Waders & shorebirds
    "american egret", "bittern", "crane", "dowitcher", "european gallinule",
    "flamingo", "limpkin", "little blue heron", "oystercatcher",
    "red-backed sandpiper", "redshank", "ruddy turnstone", "spoonbill",
    # Seabirds
    "albatross", "black-footed albatross", "black stork", "frigatebird",
    "king penguin", "pelican", "white stork",
    # Tropical / exotic
    "bee eater", "coucal", "hornbill", "hummingbird", "jacamar",
    "lorikeet", "motmot", "sunbird", "toucan",
    # Waterfowl & game birds
    "black grouse", "black swan", "bustard", "drake", "goose",
    "grouse", "partridge", "peacock", "prairie chicken", "ptarmigan",
    "quail", "red-breasted merganser", "ruffed grouse",
    # Other
    "ostrich", "pigeon",
})

# Below this confidence the model is essentially guessing — likely a non-bird photo.
BIRD_CONFIDENCE_THRESHOLD = 0.10


def passes_bird_gate(label: str, confidence: float) -> bool:
    """
    Return True only if the model is confident it saw a bird.

    Both conditions must be true:
      1. The predicted label is one of the ~57 ImageNet bird classes.
      2. Confidence is above the minimum threshold (not a wild guess).

    This rejects dog photos, food photos, and anything else that isn't a bird
    before any Singapore-specific logic runs.
    """
    normalised = label.lower().strip()
    label_is_a_bird = (
        normalised in IMAGENET_BIRD_CLASSES
        or any(bird in normalised or normalised in bird for bird in IMAGENET_BIRD_CLASSES)
    )
    return label_is_a_bird and confidence >= BIRD_CONFIDENCE_THRESHOLD
