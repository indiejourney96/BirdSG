# species_mapping.py

SPECIES_MAP = {
    "zebra_dove": {
        "common_name": "Zebra Dove",
        "ebird_code": "zebdov",
    },

    "spotted_dove": {
        "common_name": "Spotted Dove",
        "ebird_code": "spodov",
    },

    "oriental_turtle_dove": {
        "common_name": "Oriental Turtle-Dove",
        "ebird_code": "ortdov",
    },

    "yellow_vented_bulbul": {
        "common_name": "Yellow-vented Bulbul",
        "ebird_code": "yevbul1",
    },

    "olive_backed_sunbird": {
        "common_name": "Olive-backed Sunbird",
        "ebird_code": "olbsun4",
    },

    "oriental_pied_hornbill": {
        "common_name": "Oriental Pied Hornbill",
        "ebird_code": "orphor1",
    },
}
def get_species(label: str):
    return SPECIES_MAP.get(label.lower().strip())


def get_ebird_code(label: str):
    species = get_species(label)
    return species["ebird_code"] if species else None

def is_singapore_species(label: str) -> bool:
    species = get_species(label)
    return species and "SG" in species.get("regions", [])