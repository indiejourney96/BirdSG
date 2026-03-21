"""
bird_labels.py — ImageNet bird class labels and non-bird detection gate.

ImageNet-1k contains ~57 genuine bird classes out of 1000 total.
This module defines that exact set and exposes is_bird_image(), which is
called before Singapore filtering to reject non-bird uploads early.

NOTE ON MISSING LABELS
"kingfisher", "swallow", "swift", "sparrow", "warbler" are NOT ImageNet-1k
classes — the model will never output these labels. If any of these appear
in predictions it is because they matched via substring in singapore_birds.py,
not from the model itself.
"""

# All genuine bird classes in ImageNet-1k.
# Sourced from the WordNet synsets used by torchvision EfficientNet_B0_Weights.DEFAULT.
IMAGENET_BIRD_LABELS: frozenset[str] = frozenset({
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

# Minimum confidence to trust the top prediction.
# Below this the model is essentially guessing — likely a non-bird photo.
BIRD_CONFIDENCE_THRESHOLD = 0.10


def is_bird_image(label: str, confidence: float) -> bool:
    """
    Return True if the top prediction is a known bird class with enough confidence.

    Two conditions must both be true:
      1. The label exists in IMAGENET_BIRD_LABELS (rejects "suit", "person", etc.)
      2. Confidence >= BIRD_CONFIDENCE_THRESHOLD (rejects low-confidence noise)
    """
    label_lower = label.lower().strip()

    in_bird_set = (
        label_lower in IMAGENET_BIRD_LABELS
        or any(b in label_lower or label_lower in b for b in IMAGENET_BIRD_LABELS)
    )

    return in_bird_set and confidence >= BIRD_CONFIDENCE_THRESHOLD
