"""
label_map.py — ImageNet label → eBird species code mapping.

Only ImageNet labels that the model can actually output are mapped here.
Each maps to the most commonly recorded Singapore species for that label,
based on eBird frequency data for region SG.

eBird species codes are 6-char strings from the eBird taxonomy:
    https://api.ebird.org/v2/ref/taxonomy/ebird

MAPPING QUALITY
---------------
Mappings are tagged as one of:
  [EXACT]   — ImageNet label directly corresponds to a real SG species category.
              High confidence. e.g. "bulbul" → Yellow-vented Bulbul.
  [APPROX]  — Label has a plausible visual or ecological similarity to the SG
              species but is not a direct match. Use with caution.
              e.g. "hummingbird" → Olive-backed Sunbird (both small nectar feeders).
  [FORCED]  — No genuine SG equivalent. Mapped to the closest SG bird by
              general appearance only. Low confidence — treat as a best guess.
              e.g. "junco" → Eurasian Tree Sparrow (both are small brown passerines).
  [NONE]    — No reasonable SG mapping exists. Returns 404.

TODO: Replace [FORCED] and [APPROX] mappings once a Singapore-specific model
is trained. At that point, model labels will be actual SG species names and
this entire file can be replaced with a direct name → eBird code lookup.
"""

# ImageNet label (lowercase) → eBird species code for most common SG species
LABEL_TO_EBIRD_CODE: dict[str, str | None] = {

    # ── Passerines ─────────────────────────────────────────────────────────
    "bulbul":                  "yevbul1",   # [EXACT]   Yellow-vented Bulbul
    "magpie":                  "ormaro1",   # [APPROX]  Oriental Magpie-Robin — similar black-and-white plumage
    "robin":                   "ormaro1",   # [APPROX]  Oriental Magpie-Robin — ImageNet robin ≠ SG robin
    "starling":                "commy1",    # [APPROX]  Common Myna — most visible SG "starling-like" bird
    "jay":                     "bknori1",   # [APPROX]  Black-naped Oriole — colourful perching bird
    "wren":                    "comtai1",   # [APPROX]  Common Tailorbird — small, skulking, similar behaviour
    "goldfinch":               "scabfl1",   # [APPROX]  Scarlet-backed Flowerpecker — small, colourful
    "indigo bunting":          "olbsun1",   # [APPROX]  Olive-backed Sunbird — small, colourful passerine
    "yellow-headed blackbird": "bknori1",   # [APPROX]  Black-naped Oriole — yellow-and-black bird
    "junco":                   "eurtrs1",   # [FORCED]  Eurasian Tree Sparrow — junco is American, not in SG
    "brambling":               "eurtrs1",   # [FORCED]  Eurasian Tree Sparrow — European finch, unrelated
    "house finch":             "eurtrs1",   # [FORCED]  Eurasian Tree Sparrow — American species, not in SG
    "chickadee":               "eurtrs1",   # [FORCED]  Eurasian Tree Sparrow — North American, not in SG
    "water ouzel":             "whbwat1",   # [FORCED]  White-breasted Waterhen — both are waterside birds

    # ── Raptors ────────────────────────────────────────────────────────────
    "kite":                    "brakit1",   # [EXACT]   Brahminy Kite — dominant SG kite
    "vulture":                 "whbsea2",   # [APPROX]  White-bellied Sea Eagle — large soaring raptor
    "bald eagle":              "whbsea2",   # [APPROX]  White-bellied Sea Eagle — closest large eagle in SG

    # ── Waders & shorebirds ────────────────────────────────────────────────
    "crane":                   "gryher1",   # [APPROX]  Grey Heron — tall wading bird, most visible in SG
    "bittern":                 "yelbil1",   # [EXACT]   Yellow Bittern — most common SG bittern
    "redshank":                "comred2",   # [EXACT]   Common Redshank
    "dowitcher":               "asidow1",   # [EXACT]   Asian Dowitcher
    "ruddy turnstone":         "rudtur1",   # [EXACT]   Ruddy Turnstone
    "red-backed sandpiper":    "cursan1",   # [APPROX]  Curlew Sandpiper — common SG sandpiper
    "american egret":          "greegr1",   # [APPROX]  Great Egret — direct visual equivalent
    "little blue heron":       "litegr1",   # [APPROX]  Little Egret — closest small white heron in SG
    "european gallinule":      "eurmoo1",   # [APPROX]  Eurasian Moorhen — same genus
    "oystercatcher":           "pacgpl1",   # [FORCED]  Pacific Golden Plover — both are coastal shorebirds
    "limpkin":                 "whbwat1",   # [FORCED]  White-breasted Waterhen — both wade in freshwater
    "spoonbill":               "milsto1",   # [FORCED]  Milky Stork — both are large white wading birds
    "flamingo":                "milsto1",   # [FORCED]  Milky Stork — both are large pink-white waders
    "pelican":                 "lesadj1",   # [FORCED]  Lesser Adjutant — both are large waterbirds

    # ── Seabirds ───────────────────────────────────────────────────────────
    "frigatebird":             "lesfri1",   # [EXACT]   Lesser Frigatebird — recorded in SG
    "albatross":               "whttrn2",   # [FORCED]  Whiskered Tern — closest common SG seabird
    "black-footed albatross":  "whttrn2",   # [FORCED]  Whiskered Tern — no albatross in SG
    "black stork":             "lesadj1",   # [FORCED]  Lesser Adjutant — both are large dark waterbirds
    "white stork":             "milsto1",   # [FORCED]  Milky Stork — both are large white storks
    "king penguin":            None,        # [NONE]    No SG equivalent

    # ── Tropical / exotic ──────────────────────────────────────────────────
    "hornbill":                "orphor1",   # [EXACT]   Oriental Pied Hornbill — only common SG hornbill
    "bee eater":               "bltbee1",   # [EXACT]   Blue-throated Bee-eater — most common SG bee-eater
    "coucal":                  "gresco1",   # [EXACT]   Greater Coucal
    "sunbird":                 "olbsun1",   # [EXACT]   Olive-backed Sunbird — most common SG sunbird
    "lorikeet":                "blchan1",   # [APPROX]  Blue-crowned Hanging Parrot — small SG parrot
    "hummingbird":             "olbsun1",   # [APPROX]  Olive-backed Sunbird — both small nectar feeders
    "jacamar":                 "colkin1",   # [FORCED]  Collared Kingfisher — both perch and hunt insects
    "motmot":                  "colkin1",   # [FORCED]  Collared Kingfisher — similar long-tailed profile
    "toucan":                  "copbar1",   # [FORCED]  Coppersmith Barbet — both have large colourful bills

    # ── Waterfowl & game birds ─────────────────────────────────────────────
    "goose":                   "leswhi1",   # [APPROX]  Lesser Whistling Duck — most common SG waterfowl
    "drake":                   "leswhi1",   # [APPROX]  Lesser Whistling Duck
    "black swan":              "leswhi1",   # [APPROX]  Lesser Whistling Duck — both are dark waterfowl
    "quail":                   "blbqua1",   # [EXACT]   Blue-breasted Quail — only common SG quail
    "partridge":               "redjun4",   # [APPROX]  Red Junglefowl — both ground-dwelling game birds
    "peacock":                 "redjun4",   # [APPROX]  Red Junglefowl — both are large ground birds
    "pigeon":                  "spodov1",   # [EXACT]   Spotted Dove — most common SG dove/pigeon
    "bustard":                 "gryhea3",   # [FORCED]  Grey-headed Swamphen — both are large ground birds
    "grouse":                  "redjun4",   # [FORCED]  Red Junglefowl — grouse not found in SG
    "black grouse":            "redjun4",   # [FORCED]  Red Junglefowl — grouse not found in SG
    "ruffed grouse":           "redjun4",   # [FORCED]  Red Junglefowl — grouse not found in SG
    "prairie chicken":         "redjun4",   # [FORCED]  Red Junglefowl — American species, not in SG
    "ptarmigan":               "redjun4",   # [FORCED]  Red Junglefowl — Arctic species, not in SG
    "red-breasted merganser":  "leswhi1",   # [FORCED]  Lesser Whistling Duck — both are diving waterfowl
    "ostrich":                 None,        # [NONE]    No SG equivalent
}


def get_ebird_code(label: str) -> str | None:
    """
    Return the eBird species code for a given ImageNet label.
    Returns None if no reasonable SG mapping exists ([NONE] entries).
    """
    return LABEL_TO_EBIRD_CODE.get(label.lower().strip())