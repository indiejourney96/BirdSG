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
# Species list: (common_name, taxon_id)
# SPECIES = [
#     ("Spotted Dove", 1455918), 
#     ("Asian Koel", 204510),
#     ("Blue-breasted Quail", 505884),
#     ("Common Myna", 204454),
#     ("Zebra Dove", 3607),
#     # Add more species as needed
# ]
SPECIES = [
    ("Wandering Whistling-Duck", 6896), 
    ("Lesser Whistling-Duck", 6891),
    ("Cotton Pygmy-Goose", 7128),
    ("Garganey", 558429),
    ("Northern Shoveler", 558438),
    ("Gadwall", 558439),
    ("Eurasian Wigeon", 558441),
    ("Northern Pintail", 6933),
    ("Green-winged Teal", 6937),
    ("Tufted Duck", 7046),
    ("Red Junglefowl", 882),
    ("Little Grebe", 4237),
    ("Rock Pigeon", 3017),
    ("Oriental Turtle-Dove", 2927),
    ("Asian Emerald Dove", 508097),
    ("Little Green-Pigeon", 3423),
    ("Pink-necked Green-Pigeon", 3393),
    ("Cinnamon-headed Green-Pigeon", 3384),
    ("Orange-breasted Green-Pigeon", 3394),
    ("Thick-billed Green-Pigeon", 3358),
    ("Jambu Fruit Dove", 1650573),
    ("Green Imperial Pigeon", 3211),
    ("Mountain Imperial Pigeon", 3246),
    ("Pied Imperial Pigeon", 3255),
    # Add more species as needed
]
PLACE_IDS = [6734, 7155, 6966]  # Singapore + Malaysia + Indonesia
# ---------------- FUNCTIONS ----------------
def download_species(species_name, taxon_id):
    print(f"\nDownloading {species_name}")
    
    # Create folder for species
    folder_name = species_name.lower().replace(" ", "_")
    save_dir = Path(OUTPUT_DIR) / folder_name
    save_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    page_map = {pid: 1 for pid in PLACE_IDS}  # track page per place
    
    while count < IMAGES_PER_SPECIES:
        all_empty = True  # stop if all places exhausted
    
        for place_id in PLACE_IDS:
            if count >= IMAGES_PER_SPECIES:
             break

            url = "https://api.inaturalist.org/v1/observations"
            params = {
                "taxon_id": taxon_id,
                "place_id": place_id,
                "quality_grade": "research,needs_id",
                "photos": "true",
                "per_page": PER_PAGE,
                "page": page_map[place_id]
            }

            try:
                response = requests.get(url, params=params).json()
            except Exception as e:
                print("Request failed:", e)
                continue

            results = response.get("results", [])
            if not results:
                continue

            all_empty = False

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

            page_map[place_id] += 1
            time.sleep(1)

        if all_empty:
            print(f"No more results from all places for {species_name}.")
            break


# ---------------- MAIN ----------------
for species_name, taxon_id in SPECIES:
    download_species(species_name, taxon_id)

print("\nAll downloads complete.")