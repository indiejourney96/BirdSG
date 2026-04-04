import os
import requests
from pathlib import Path
import time

# ---------------- CONFIG ----------------
OUTPUT_DIR = "dataset"
IMAGES_PER_SPECIES = 50  # max images per species per run
PER_PAGE = 100  # max per API request
# Allowed licenses
ALLOWED_LICENSES = ["cc0", "cc-by", "cc-by-sa"]
# Species list: (common_name, taxon_id)
SPECIES = [
    ("Spotted Dove", 1455918), 
    ("Asian Koel", 204510),
    ("Blue-breasted Quail", 505884),
    ("Common Myna", 204454),
    ("Zebra Dove", 3607),
    # Add more species as needed
]
PLACE_ID = 6734  # Singapore
# ---------------- FUNCTIONS ----------------
def download_species(species_name, taxon_id):
    print(f"\nDownloading {species_name}")
    
    # Create folder for species
    folder_name = species_name.lower().replace(" ", "_")
    save_dir = Path(OUTPUT_DIR) / folder_name
    save_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    page = 1
    
    while count < IMAGES_PER_SPECIES:
        url = "https://api.inaturalist.org/v1/observations"
        params = {
            "taxon_id": taxon_id,
            "place_id": PLACE_ID,
            "quality_grade": "research,needs_id",
            "photos": "true",
            "per_page": PER_PAGE,
            "page": page
        }
        
        try:
            response = requests.get(url, params=params).json()
        except Exception as e:
            print("Request failed:", e)
            break
        
        # Safety check
        if "results" not in response or len(response["results"]) == 0:
            print(f"No more results found for {species_name}.")
            break
            
        for result in response["results"]:
            if count >= IMAGES_PER_SPECIES:
                break
            
            for photo in result.get("photos", []):
                license_code = photo.get("license_code")
                if license_code not in ALLOWED_LICENSES:
                    continue
                
                # Use large version of image
                img_url = photo["url"].replace("square", "large")
                
                try:
                    img_data = requests.get(img_url).content
                    # ✅ FIXED: Use proper naming format
                    # Extract a simple number from the API result or use sequential counter
                    # For now, use sequential counter with species name
                    file_path = save_dir / f"{count}_{folder_name}.png"
                    
                    with open(file_path, "wb") as f:
                        f.write(img_data)
                    
                    count += 1
                    print(f"Saved {file_path}")
                    
                except Exception as e:
                    print("Failed to download image:", e)
                    
                if count >= IMAGES_PER_SPECIES:
                    break

        page += 1
        time.sleep(1)  # polite delay to avoid rate-limiting

    print(f"Finished downloading {count} images for {species_name}.")


# ---------------- MAIN ----------------
for species_name, taxon_id in SPECIES:
    download_species(species_name, taxon_id)

print("\nAll downloads complete.")