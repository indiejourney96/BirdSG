import os
import json
import time
import requests
from pathlib import Path

from app.sg_species import ALL_SINGAPORE_SPECIES

# ---------------- CONFIG ----------------
OUTPUT_DIR = "dataset"
IMAGES_PER_SPECIES = 150
PER_PAGE = 100

MODE = "global"  # "global" or "regional"

PLACE_IDS = [6734, 7155, 6966]  # SG, MY, ID

ALLOWED_LICENSES = {"cc0", "cc-by", "cc-by-sa"}

CACHE_FILE = "taxon_cache.json"

# ---------------- CACHE ----------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

taxon_cache = load_cache()

# ---------------- HELPERS ----------------
def normalize_name(name: str) -> str:
    return name.lower().replace("-", " ").strip()

def get_taxon_id(species_name):
    if species_name in taxon_cache:
        return taxon_cache[species_name]

    url = "https://api.inaturalist.org/v1/taxa"
    params = {
        "q": species_name,
        "rank": "species",
        "per_page": 5
    }

    try:
        response = requests.get(url, params=params).json()
        results = response.get("results", [])

        if not results:
            print(f"❌ No taxon found: {species_name}")
            return None

        target = normalize_name(species_name)

        # 1. Exact match
        for taxon in results:
            name = normalize_name(taxon.get("preferred_common_name", ""))
            if name == target:
                taxon_cache[species_name] = taxon["id"]
                save_cache(taxon_cache)
                return taxon["id"]

        # 2. Loose match
        for taxon in results:
            name = normalize_name(taxon.get("preferred_common_name", ""))
            if target in name or name in target:
                taxon_cache[species_name] = taxon["id"]
                save_cache(taxon_cache)
                return taxon["id"]

        # 3. Fallback
        fallback = results[0]["id"]
        print(f"⚠️ Fallback match: {species_name}")
        taxon_cache[species_name] = fallback
        save_cache(taxon_cache)
        return fallback

    except Exception as e:
        print(f"Error fetching taxon for {species_name}: {e}")
        return None


# def has_enough_data(taxon_id):
#     url = "https://api.inaturalist.org/v1/observations"
#     params = {"taxon_id": taxon_id, "per_page": 1}

#     try:
#         response = requests.get(url, params=params).json()
#         return response.get("total_results", 0) >= MIN_RESULTS
#     except:
#         return False


def fetch_results(taxon_id, page, place_id=None):
    url = "https://api.inaturalist.org/v1/observations"

    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research,needs_id",
        "photos": "true",
        "per_page": PER_PAGE,
        "page": page
    }

    if place_id:
        params["place_id"] = place_id

    try:
        return requests.get(url, params=params).json()
    except:
        return {}


def download_image(url, path):
    try:
        img_data = requests.get(url).content
        with open(path, "wb") as f:
            f.write(img_data)
        return True
    except:
        return False


# ---------------- CORE ----------------
def process_results(results, save_dir, prefix, count):
    for result in results:
        if count >= IMAGES_PER_SPECIES:
            break

        for photo in result.get("photos", []):
            if count >= IMAGES_PER_SPECIES:
                break

            if photo.get("license_code") not in ALLOWED_LICENSES:
                continue

            img_url = photo["url"].replace("square", "large")
            file_path = save_dir / f"{count}_{prefix}.jpg"

            if download_image(img_url, file_path):
                count += 1
                print(f"Saved {file_path}")

    return count


def download_species(species_name, taxon_id):
    print(f"\n⬇️ Downloading {species_name} ({MODE})")

    folder = species_name.lower().replace(" ", "_")
    save_dir = Path(OUTPUT_DIR) / folder
    save_dir.mkdir(parents=True, exist_ok=True)

    count = 0

    if MODE == "regional":
        page_map = {pid: 1 for pid in PLACE_IDS}

        while count < IMAGES_PER_SPECIES:
            all_empty = True

            for pid in PLACE_IDS:
                if count >= IMAGES_PER_SPECIES:
                    break

                response = fetch_results(taxon_id, page_map[pid], pid)
                results = response.get("results", [])

                if not results:
                    continue

                all_empty = False
                count = process_results(results, save_dir, folder, count)

                page_map[pid] += 1
                time.sleep(0.5)

            if all_empty:
                break

    elif MODE == "global":
        page = 1

        while count < IMAGES_PER_SPECIES:
            response = fetch_results(taxon_id, page)
            results = response.get("results", [])

            if not results:
                break

            count = process_results(results, save_dir, folder, count)

            page += 1
            time.sleep(0.5)

    print(f"✅ Done {species_name}: {count} images")


# ---------------- MAIN ----------------
def main():
    for species_name in ALL_SINGAPORE_SPECIES:
        taxon_id = get_taxon_id(species_name)

        if not taxon_id:
            continue

        # if not has_enough_data(taxon_id):
        #     print(f"⏭️ Skipping {species_name} (low data)")
        #     continue

        download_species(species_name, taxon_id)
        time.sleep(1)

    print("\n🎉 All downloads complete.")


if __name__ == "__main__":
    main()