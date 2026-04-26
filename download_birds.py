import os
import requests
from pathlib import Path
import time

# ---------------- CONFIG ----------------
OUTPUT_DIR = "dataset"
IMAGES_PER_SPECIES = 100  # max images per species per run
PER_PAGE = 100  # max per API request
# Allowed licenses
ALLOWED_LICENSES = ["cc0", "cc-by", "cc-by-sa"]


MODE = "global"  # "global" or "regional"
# Species list: (common_name, taxon_id)
# SPECIES = [
#     ("Spotted Dove", 1455918), 
#     ("Asian Koel", 204510),
#     ("Blue-breasted Quail", 505884),
#     ("Common Myna", 204454),
#     ("Zebra Dove", 3607),
#     ("Rock Pigeon", 3017),
#     ("Red Junglefowl", 882),
#     ("Green Imperial Pigeon", 3211),
#     ("Asian Emerald Dove", 508097),
#     ("Wandering Whistling-Duck", 6896), 
#     ("Lesser Whistling-Duck", 6891),
#     ("Cotton Pygmy-Goose", 7128),
#     ("Garganey", 558429),
#     ("Northern Shoveler", 558438),
#     ("Gadwall", 558439),
#     ("Eurasian Wigeon", 558441),
#     ("Northern Pintail", 6933),
#     ("Green-winged Teal", 6937),
#     ("Tufted Duck", 7046),
#     ("Little Grebe", 4237),
#     ("Oriental Turtle-Dove", 2927),
#     ("Little Green-Pigeon", 3423),
#     ("Pink-necked Green-Pigeon", 3393),
#     ("Cinnamon-headed Green-Pigeon", 3384),
#     ("Orange-breasted Green-Pigeon", 3394),
#     ("Thick-billed Green-Pigeon", 3358),
#     ("Jambu Fruit Dove", 1650573),
#     ("Mountain Imperial Pigeon", 3246),
#     ("Pied Imperial Pigeon", 3255),
#     ("Blue-breasted Quail", 505884),
#     # Add more species as needed
# ]
SPECIES = [
    ("Greater Coucal", 1677),
    ("Lesser Coucal", 1644),
    ("Chestnut-bellied Malkoha", 73190),
    ("Chestnut-bellied Cuckoo", 72744),
    ("Pied Cuckoo", 1789),
    ("Asian Emerald Cuckoo", 1728),
    ("Violet Cuckoo", 1720),
    ("Horsfield's Bronze Cuckoo", 1578710),
    ("Little Bronze Cuckoo", 369157),
    ("Banded Bay Cuckoo", 1827),
    ("Violet Cuckoo", 1827),
    ("Plaintive Cuckoo", 1856),
    ("Sunda Brush Cuckoo", 96387),
    ("Square-tailed Drongo-Cuckoo", 1930),
    ("Large Hawk-Cuckoo", 567164),
    ("Hodgson's Hawk-Cuckoo", 144577),
    ("Malaysian Hawk-Cuckoo", 144579),
    ("Indian Cuckoo", 1904),
    ("Himalayan Cuckoo", 1899),
    ("Malaysian Eared Nightjar", 201063),
    ("Gray Nightjar", 367509),
    ("Savanna Nightjar", 19466),
    # Add more species as needed
]

# Only used if MODE = "regional"
PLACE_IDS = [6734, 7155, 6966]  # Singapore + Malaysia + Indonesia

# ---------------- FUNCTIONS ----------------
def fetch_results(taxon_id, page, place_id=None):
    url = "https://api.inaturalist.org/v1/observations"

    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research,needs_id",
        "photos": "true",
        "per_page": PER_PAGE,
        "page": page
    }

    if place_id is not None:
        params["place_id"] = place_id

    try:
        return requests.get(url, params=params).json()
    except Exception as e:
        print("Request failed:", e)
        return {}


def download_species(species_name, taxon_id):
    print(f"\nDownloading {species_name} ({MODE})")

    folder_name = species_name.lower().replace(" ", "_")
    save_dir = Path(OUTPUT_DIR) / folder_name
    save_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    if MODE == "regional":
        page_map = {pid: 1 for pid in PLACE_IDS}

        while count < IMAGES_PER_SPECIES:
            all_empty = True

            for place_id in PLACE_IDS:
                if count >= IMAGES_PER_SPECIES:
                    break

                response = fetch_results(
                    taxon_id,
                    page_map[place_id],
                    place_id=place_id
                )

                results = response.get("results", [])
                if not results:
                    continue

                all_empty = False

                count = process_results(results, save_dir, folder_name, count)

                page_map[place_id] += 1
                time.sleep(1)

            if all_empty:
                print(f"No more results from all places for {species_name}.")
                break

    elif MODE == "global":
        page = 1

        while count < IMAGES_PER_SPECIES:
            response = fetch_results(taxon_id, page)

            results = response.get("results", [])
            if not results:
                print(f"No more global results for {species_name}.")
                break

            count = process_results(results, save_dir, folder_name, count)

            page += 1
            time.sleep(1)

    else:
        raise ValueError("MODE must be 'global' or 'regional'")


def process_results(results, save_dir, folder_name, count):
    for result in results:
        if count >= IMAGES_PER_SPECIES:
            break

        for photo in result.get("photos", []):
            license_code = photo.get("license_code")
            if license_code not in ALLOWED_LICENSES:
                continue

            img_url = photo["url"].replace("square", "large")

            try:
                img_data = requests.get(img_url).content
                file_path = save_dir / f"{count}_{folder_name}.png"

                with open(file_path, "wb") as f:
                    f.write(img_data)

                count += 1
                print(f"Saved {file_path}")

            except Exception as e:
                print("Failed:", e)

            if count >= IMAGES_PER_SPECIES:
                break

    return count


# ---------------- MAIN ----------------
for species_name, taxon_id in SPECIES:
    download_species(species_name, taxon_id)

print("\nAll downloads complete.")