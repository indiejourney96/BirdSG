"""
singapore_birds.py — Static Singapore species list and filtering logic.

SOURCE: Wikipedia "List of birds of Singapore" (Clements Checklist 2023b),
        cross-referenced with the Singapore Bird Records Committee checklist
        at records.singaporebirds.com and the iNaturalist guide #1161.

HOW TO REPLACE THIS WITH LIVE eBIRD DATA (Phase 3 upgrade)
------------------------------------------------------------
The eBird API (https://documenter.getbirdpages.com/ebird) provides a
real-time species list for any region. Replace the static list below with
a dynamic fetch like this:

    import httpx

    EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")
    EBIRD_REGION  = "SG"          # ISO country code for Singapore

    async def fetch_singapore_species() -> set[str]:
        url = f"https://api.ebird.org/v2/product/spplist/{EBIRD_REGION}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"X-eBirdApiToken": EBIRD_API_KEY})
            species_codes = resp.json()           # e.g. ["asakoe1", "comkif1", ...]

        # Map eBird species codes → common names via /v2/ref/taxonomy/ebird
        taxon_url = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json&locale=en"
        async with httpx.AsyncClient() as client:
            taxa = await client.get(taxon_url, headers={"X-eBirdApiToken": EBIRD_API_KEY})
            taxonomy = {t["speciesCode"]: t["comName"] for t in taxa.json()}

        return {taxonomy[code].lower() for code in species_codes if code in taxonomy}

Then call fetch_singapore_species() inside the lifespan() in main.py and
cache the result (e.g. in a module-level set or a Redis key).

Filtering call in predict.py stays exactly the same — only the source
of SG_SPECIES_LOWER changes from static → dynamic.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Full Singapore bird species list — 445 species (resident, migrant, vagrant,
# introduced). Common names follow IOC / Clements 2023b conventions used by
# the Singapore Bird Records Committee.
# ---------------------------------------------------------------------------

SINGAPORE_SPECIES: list[str] = [
    # Waterfowl (Anatidae)
    "Wandering Whistling Duck",
    "Lesser Whistling Duck",
    "Cotton Pygmy Goose",
    "Garganey",
    "Northern Shoveler",
    "Gadwall",
    "Eurasian Wigeon",
    "Northern Pintail",
    "Green-winged Teal",
    "Tufted Duck",
    # Landfowl (Phasianidae)
    "Blue-breasted Quail",
    "Red Junglefowl",
    # Grebes (Podicipedidae)
    "Little Grebe",
    # Pigeons & Doves (Columbidae)
    "Rock Pigeon",
    "Oriental Turtle Dove",
    "Red Collared Dove",
    "Spotted Dove",
    "Asian Emerald Dove",
    "Zebra Dove",
    "Little Green Pigeon",
    "Pink-necked Green Pigeon",
    "Cinnamon-headed Green Pigeon",
    "Orange-breasted Green Pigeon",
    "Thick-billed Green Pigeon",
    "Jambu Fruit Dove",
    "Green Imperial Pigeon",
    "Mountain Imperial Pigeon",
    "Pied Imperial Pigeon",
    # Cuckoos (Cuculidae)
    "Greater Coucal",
    "Lesser Coucal",
    "Chestnut-bellied Malkoha",
    "Chestnut-winged Cuckoo",
    "Pied Cuckoo",
    "Asian Koel",
    "Asian Emerald Cuckoo",
    "Violet Cuckoo",
    "Horsfield's Bronze Cuckoo",
    "Little Bronze Cuckoo",
    "Banded Bay Cuckoo",
    "Plaintive Cuckoo",
    "Brush Cuckoo",
    "Square-tailed Drongo Cuckoo",
    "Large Hawk Cuckoo",
    "Hodgson's Hawk Cuckoo",
    "Malaysian Hawk Cuckoo",
    "Indian Cuckoo",
    "Himalayan Cuckoo",
    # Nightjars (Caprimulgidae)
    "Malaysian Eared Nightjar",
    "Grey Nightjar",
    "Large-tailed Nightjar",
    "Savanna Nightjar",
    # Swifts (Apodidae)
    "Silver-rumped Needletail",
    "White-throated Needletail",
    "Silver-backed Needletail",
    "Brown-backed Needletail",
    "Plume-toed Swiftlet",
    "Black-nest Swiftlet",
    "Germain's Swiftlet",
    "Common Swift",
    "Pacific Swift",
    "House Swift",
    "Asian Palm Swift",
    # Treeswifts (Hemiprocnidae)
    "Grey-rumped Treeswift",
    "Whiskered Treeswift",
    # Rails & Crakes (Rallidae)
    "Slaty-breasted Rail",
    "Eurasian Moorhen",
    "Eurasian Coot",
    "Black-backed Swamphen",
    "Grey-headed Swamphen",
    "Watercock",
    "White-breasted Waterhen",
    "White-browed Crake",
    "Red-legged Crake",
    "Slaty-legged Crake",
    "Ruddy-breasted Crake",
    "Band-bellied Crake",
    "Baillon's Crake",
    "Masked Finfoot",
    "Barred Buttonquail",
    # Shorebirds — Thick-knees, Stilts, Plovers
    "Beach Thick Knee",
    "Black-winged Stilt",
    "Pied Stilt",
    "Black-bellied Plover",
    "Pacific Golden Plover",
    "Grey-headed Lapwing",
    "Red-wattled Lapwing",
    "Masked Lapwing",
    "Tibetan Sand Plover",
    "Greater Sand Plover",
    "Malaysian Plover",
    "Kentish Plover",
    "White-faced Plover",
    "Javan Plover",
    "Common Ringed Plover",
    "Little Ringed Plover",
    "Oriental Plover",
    "Greater Painted Snipe",
    "Pheasant-tailed Jacana",
    "Oriental Pratincole",
    "Small Pratincole",
    # Skuas & Jaegers (Stercorariidae)
    "Pomarine Jaeger",
    "Parasitic Jaeger",
    "Long-tailed Jaeger",
    # Gulls & Terns (Laridae)
    "Black-headed Gull",
    "Brown-headed Gull",
    "Lesser Black-backed Gull",
    "Bridled Tern",
    "Aleutian Tern",
    "Little Tern",
    "Gull-billed Tern",
    "Caspian Tern",
    "White-winged Tern",
    "Whiskered Tern",
    "Roseate Tern",
    "Black-naped Tern",
    "Common Tern",
    "Great Crested Tern",
    "Lesser Crested Tern",
    # Tropicbirds (Phaethontidae)
    "Red-billed Tropicbird",
    "White-tailed Tropicbird",
    # Tubenoses (Procellariidae / Hydrobatidae)
    "Swinhoe's Storm Petrel",
    "Bulwer's Petrel",
    "Short-tailed Shearwater",
    "Wedge-tailed Shearwater",
    # Storks (Ciconiidae)
    "Asian Openbill",
    "Lesser Adjutant",
    "Milky Stork",
    "Painted Stork",
    # Frigatebirds, Boobies, Cormorants (Suliformes)
    "Lesser Frigatebird",
    "Christmas Island Frigatebird",
    "Brown Booby",
    "Red-footed Booby",
    "Oriental Darter",
    "Great Cormorant",
    # Herons & Egrets (Ardeidae)
    "Yellow Bittern",
    "Schrenck's Bittern",
    "Cinnamon Bittern",
    "Black Bittern",
    "Grey Heron",
    "Great-billed Heron",
    "Purple Heron",
    "Great Egret",
    "Medium Egret",
    "Chinese Egret",
    "Little Egret",
    "Pacific Reef Heron",
    "Eastern Cattle Egret",
    "Indian Pond Heron",
    "Chinese Pond Heron",
    "Javan Pond Heron",
    "Striated Heron",
    "Black-crowned Night Heron",
    "Malayan Night Heron",
    # Ibises & Spoonbills (Threskiornithidae)
    "Glossy Ibis",
    "Black-headed Ibis",
    # Osprey (Pandionidae)
    "Osprey",
    # Hawks, Eagles & Kites (Accipitridae)
    "Black-winged Kite",
    "Oriental Honey Buzzard",
    "Jerdon's Baza",
    "Black Baza",
    "Cinereous Vulture",
    "Himalayan Griffon",
    "Crested Serpent Eagle",
    "Short-toed Snake Eagle",
    "Bat Hawk",
    "Changeable Hawk Eagle",
    "Rufous-bellied Eagle",
    "Greater Spotted Eagle",
    "Booted Eagle",
    "Steppe Eagle",
    "Eastern Imperial Eagle",
    "Grey-faced Buzzard",
    "Eastern Marsh Harrier",
    "Hen Harrier",
    "Pied Harrier",
    "Crested Goshawk",
    "Shikra",
    "Chinese Sparrowhawk",
    "Japanese Sparrowhawk",
    "Besra",
    "Eurasian Sparrowhawk",
    "Black Kite",
    "Brahminy Kite",
    "White-bellied Sea Eagle",
    "Grey-headed Fish Eagle",
    "Common Buzzard",
    "Himalayan Buzzard",
    "Eastern Buzzard",
    "Long-legged Buzzard",
    # Owls (Strigidae / Tytonidae)
    "Eastern Barn Owl",
    "Collared Scops Owl",
    "Oriental Scops Owl",
    "Barred Eagle Owl",
    "Buffy Fish Owl",
    "Spotted Wood Owl",
    "Brown Wood Owl",
    "Long-eared Owl",
    "Short-eared Owl",
    "Brown Boobook",
    "Northern Boobook",
    # Hornbills (Bucerotidae)
    "Rhinoceros Hornbill",
    "Black Hornbill",
    "Oriental Pied Hornbill",
    # Kingfishers (Alcedinidae)
    "Common Kingfisher",
    "Blue-eared Kingfisher",
    "Black-backed Dwarf Kingfisher",
    "Rufous-backed Dwarf Kingfisher",
    "Stork-billed Kingfisher",
    "Ruddy Kingfisher",
    "White-throated Kingfisher",
    "Black-capped Kingfisher",
    "Collared Kingfisher",
    # Bee-eaters (Meropidae)
    "Blue-throated Bee Eater",
    "Blue-tailed Bee Eater",
    # Rollers (Coraciidae)
    "Dollarbird",
    # Barbets (Megalaimidae)
    "Coppersmith Barbet",
    "Red-crowned Barbet",
    "Lineated Barbet",
    # Woodpeckers (Picidae)
    "Sunda Pygmy Woodpecker",
    "Rufous Woodpecker",
    "Buff-rumped Woodpecker",
    "Common Flameback",
    "Greater Flameback",
    "Crimson-winged Woodpecker",
    "Laced Woodpecker",
    "Banded Woodpecker",
    "Great Slaty Woodpecker",
    "White-bellied Woodpecker",
    # Falcons (Falconidae)
    "Black-thighed Falconet",
    "Lesser Kestrel",
    "Eurasian Kestrel",
    "Amur Falcon",
    "Eurasian Hobby",
    "Peregrine Falcon",
    # Cockatoos & Parrots (Cacatuidae / Psittaculidae)
    "Tanimbar Corella",
    "Yellow-crested Cockatoo",
    "Sulphur-crested Cockatoo",
    "Blue-rumped Parrot",
    "Rose-ringed Parakeet",
    "Red-breasted Parakeet",
    "Long-tailed Parakeet",
    "Coconut Lorikeet",
    "Blue-crowned Hanging Parrot",
    # Broadbills & Pittas (Passeriformes)
    "Green Broadbill",
    "Black-and-red Broadbill",
    "Blue-winged Pitta",
    "Fairy Pitta",
    "Western Hooded Pitta",
    "Mangrove Pitta",
    # Gerygone, Minivets, Trillers, Cuckooshrikes
    "Golden-bellied Gerygone",
    "Scarlet Minivet",
    "Ashy Minivet",
    "Pied Triller",
    "Lesser Cuckooshrike",
    "White-bellied Erpornis",
    "Mangrove Whistler",
    # Orioles, Woodshrikes, Ioras, Fantails
    "Black-naped Oriole",
    "Large Woodshrike",
    "Black-winged Flycatcher Shrike",
    "Common Iora",
    "Malaysian Pied Fantail",
    # Drongos (Dicruridae)
    "Black Drongo",
    "Ashy Drongo",
    "Crow-billed Drongo",
    "Hair-crested Drongo",
    "Greater Racket-tailed Drongo",
    # Monarch Flycatchers (Monarchidae)
    "Black-naped Monarch",
    "Black Paradise Flycatcher",
    "Amur Paradise Flycatcher",
    "Blyth's Paradise Flycatcher",
    "Indian Paradise Flycatcher",
    # Shrikes (Laniidae)
    "Tiger Shrike",
    "Brown Shrike",
    "Burmese Shrike",
    "Long-tailed Shrike",
    # Crows & Jays (Corvidae)
    "Slender-billed Crow",
    "Large-billed Crow",
    "House Crow",
    # Tits (Paridae)
    "Sultan Tit",
    # Larks (Alaudidae)
    "Australasian Bushlark",
    # Swallows & Martins (Hirundinidae)
    "Barn Swallow",
    "Pacific Swallow",
    "Red-rumped Swallow",
    "Striated Swallow",
    "Asian House Martin",
    # Bulbuls (Pycnonotidae)
    "Straw-headed Bulbul",
    "Black-headed Bulbul",
    "Black-crested Bulbul",
    "Scaly-breasted Bulbul",
    "Stripe-throated Bulbul",
    "Yellow-vented Bulbul",
    "Olive-winged Bulbul",
    "Cream-vented Bulbul",
    "Red-eyed Bulbul",
    "Spectacled Bulbul",
    "Buff-vented Bulbul",
    "Ashy Bulbul",
    "Puff-backed Bulbul",
    # Leaf Warblers (Phylloscopidae)
    "Arctic Warbler",
    "Sakhalin Leaf Warbler",
    "Yellow-browed Warbler",
    "Pale-legged Leaf Warbler",
    "Two-barred Warbler",
    "Dusky Warbler",
    "Radde's Warbler",
    "Buff-throated Warbler",
    # Reed Warblers (Acrocephalidae)
    "Oriental Reed Warbler",
    "Black-browed Reed Warbler",
    "Clamorous Reed Warbler",
    "Booted Warbler",
    # Grassbirds & Cisticolas (Locustellidae / Cisticolidae)
    "Lanceolated Warbler",
    "Pallas's Grasshopper Warbler",
    "Striated Grassbird",
    "Zitting Cisticola",
    "Golden-headed Cisticola",
    "Common Tailorbird",
    "Dark-necked Tailorbird",
    "Ashy Tailorbird",
    "Rufous-tailed Tailorbird",
    # White-eyes (Zosteropidae)
    "Swinhoe's White Eye",
    "Everett's White Eye",
    # Laughingthrushes & Babblers (Leiothrichidae / Timaliidae / Pellorneidae)
    "Pin-striped Tit Babbler",
    "Bold-striped Tit Babbler",
    "Abbott's Babbler",
    "Buff-breasted Babbler",
    "Short-tailed Babbler",
    "Moustached Babbler",
    "Sooty-capped Babbler",
    "Rufous-crowned Babbler",
    "Black-throated Babbler",
    "Chestnut-winged Babbler",
    "White-chested Babbler",
    "Ferruginous Babbler",
    "Yellow-bellied Prinia",
    # Starlings (Sturnidae)
    "Asian Glossy Starling",
    "Philippine Glossy Starling",
    "Common Hill Myna",
    "Black-winged Starling",
    "Common Myna",
    "Javan Myna",
    "Vinous-breasted Starling",
    "White-shouldered Starling",
    "Chestnut-cheeked Starling",
    "Rosy Starling",
    "White-faced Starling",
    "Purple-backed Starling",
    "Daurian Starling",
    # Thrushes (Turdidae)
    "Blue Rock Thrush",
    "White-throated Rock Thrush",
    "Siberian Thrush",
    "Orange-headed Thrush",
    "Scaly Thrush",
    "Eyebrowed Thrush",
    "Dark-sided Thrush",
    "Island Thrush",
    # Old World Flycatchers (Muscicapidae)
    "Oriental Magpie Robin",
    "White-rumped Shama",
    "Mangrove Blue Flycatcher",
    "Brown-chested Jungle Flycatcher",
    "Brown-streaked Flycatcher",
    "Brown-breasted Flycatcher",
    "Spotted Flycatcher",
    "Blue-and-white Flycatcher",
    "Chinese Blue Flycatcher",
    "Mugimaki Flycatcher",
    "Narcissus Flycatcher",
    "Taiga Flycatcher",
    "Asian Brown Flycatcher",
    "Grey-streaked Flycatcher",
    "Verditer Flycatcher",
    "Large Niltava",
    "Rufous-chested Flycatcher",
    "Indigo Flycatcher",
    "Little Pied Flycatcher",
    "Siberian Blue Robin",
    "Orange-flanked Bush Robin",
    "White-tailed Robin",
    "Blue Whistling Thrush",
    "Pied Bushchat",
    "Common Stonechat",
    # Wagtails & Pipits (Motacillidae)
    "Eastern Yellow Wagtail",
    "Citrine Wagtail",
    "White Wagtail",
    "Grey Wagtail",
    "Forest Wagtail",
    "Paddyfield Pipit",
    "Tree Pipit",
    "Olive-backed Pipit",
    "Red-throated Pipit",
    "Richard's Pipit",
    # Sunbirds & Spiderhunters (Nectariniidae)
    "Crimson Sunbird",
    "Ruby-cheeked Sunbird",
    "Purple-naped Sunbird",
    "Brown-throated Sunbird",
    "Copper-throated Sunbird",
    "Olive-backed Sunbird",
    "Purple Sunbird",
    "Scarlet-backed Flowerpecker",
    "Orange-bellied Flowerpecker",
    "Yellow-vented Flowerpecker",
    "Plain Flowerpecker",
    "Thick-billed Flowerpecker",
    "Yellow-bellied Flowerpecker",
    "Little Spiderhunter",
    "Long-billed Spiderhunter",
    "Spectacled Spiderhunter",
    "Yellow-eared Spiderhunter",
    # Weavers, Munias & Sparrows (Estrildidae / Ploceidae / Passeridae)
    "Eurasian Tree Sparrow",
    "Baya Weaver",
    "Streaked Weaver",
    "Scaly-breasted Munia",
    "White-headed Munia",
    "White-bellied Munia",
    "Chestnut Munia",
    "Tricolored Munia",
    "Pin-tailed Parrotfinch",
    "Red Avadavat",
    "Java Sparrow",
    "Yellow-fronted Canary",
    # Buntings (Emberizidae)
    "Yellow-breasted Bunting",
    "Black-headed Bunting",
    "Chestnut Bunting",
    "Rustic Bunting",
    "Willow Warbler",
]

# ---------------------------------------------------------------------------
# Pre-computed lowercase set for O(1) membership testing at inference time.
# The filter function normalises both the model label and each SG species name
# to lowercase before comparing, handling capitalisation differences between
# ImageNet labels and IOC names.
# ---------------------------------------------------------------------------
SG_SPECIES_LOWER: set[str] = {s.lower() for s in SINGAPORE_SPECIES}


def is_singapore_bird(label: str) -> bool:
    """
    Return True if the ImageNet label matches a Singapore species.

    Matching strategy (in order):
      1. Exact match after lowercasing  — e.g. "bulbul" ∈ SG_SPECIES_LOWER? No.
      2. Substring match — does any SG species name contain the label word,
         or does the label contain a key SG species word?

    This handles the fact that ImageNet uses short generic names like "bulbul"
    while SG names are specific like "Yellow-vented Bulbul".
    """
    label_lower = label.lower().strip()

    # 1. Exact match
    if label_lower in SG_SPECIES_LOWER:
        return True

    # 2. Substring: any SG species whose name contains the ImageNet label
    #    e.g. label="kingfisher" matches "Collared Kingfisher", "Common Kingfisher", etc.
    for sg_name in SG_SPECIES_LOWER:
        if label_lower in sg_name or sg_name in label_lower:
            return True

    return False
