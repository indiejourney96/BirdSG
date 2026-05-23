"""
generate_bird_details.py

Output: bird_details_generated.json ready for bulk_insert_bird_details.py

Usage:
    python scripts/generate_bird_details.py --input species_mapping.json --output bird_details_generated.json
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

EBIRD_BASE = "https://api.ebird.org/v2"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
RATE_LIMIT_DELAY = 0.2  # Pause between API requests to respect servers

def get_ebird_taxonomy(ebird_code: str, api_key: str) -> dict:
    """Fetches official scientific and common names from eBird taxonomy API."""
    if not api_key:
        return {}
    
    url = f"{EBIRD_BASE}/ref/taxonomy/ebird"
    headers = {"X-eBirdApiToken": api_key}
    params = {"species": ebird_code, "fmt": "json"}
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                return data[0]
    except Exception as e:
        logger.error(f"Failed to fetch eBird taxonomy for {ebird_code}: {e}")
    return {}

def get_wikipedia_summary(title: str) -> str:
    """
    Queries the free Wikipedia API using a search term (scientific name or common name).
    Extracts the clean intro text summary before the first major heading.
    """
    if not title or title == "N/A":
        return ""
        
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,       # Restricts text to just the main intro summary
        "explaintext": True,   # Strips out HTML/Wiki markup tags for clean plain text
        "titles": title,
        "redirects": 1         # Automatically follows page redirections
    }
    
    # Wikipedia API strictly requires a descriptive User-Agent to prevent 403 Forbidden drops
    headers = {
        "User-Agent": "BirdSGApp/1.0 (daryl@hotmail.com) httpx/0.27.0"
    }
    
    try:
        response = httpx.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=10.0)
        if response.status_code == 200:
            res_data = response.json()
            pages = res_data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":  # Wikipedia returns "-1" if no matching article exists
                    extract = page_data.get("extract", "").strip()
                    # Clean up any messy newline gaps if present
                    return " ".join(extract.splitlines())
        else:
            logger.error(f"Wikipedia API returned status code {response.status_code} for '{title}'")
    except Exception as e:
        logger.error(f"Failed to fetch Wikipedia summary for '{title}': {e}")
    return ""

def main():
    parser = argparse.ArgumentParser(description="Automate generating bird profiles using eBird and Wikipedia")
    parser.add_argument("--input", default="species_mapping.json", help="Path to input mapping file")
    parser.add_argument("--output", default="bird_details_generated.json", help="Output path for bulk insert JSON")
    parser.add_argument("--ebird-key", default=os.environ.get("EBIRD_API_KEY"), help="eBird API token")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        species_mapping = json.load(f)

    # Cleanly transform dictionary maps (SPECIES_MAP) into an iterable item list
    if isinstance(species_mapping, dict):
        species_items = list(species_mapping.values())
    else:
        species_items = species_mapping

    output_data = []
    total_species = len(species_items)
    logger.info(f"Starting pipeline for {total_species} species mapping...")

    for idx, item in enumerate(species_items, start=1):
        ebird_code = item.get("ebird_code")
        common_name = item.get("common_name", "Unknown Species")
        
        if not ebird_code:
            continue
            
        # 1. Fetch live taxonomy details from eBird to secure the precise scientific name
        taxonomy_data = get_ebird_taxonomy(ebird_code, args.ebird_key)
        scientific_name = "N/A"
        
        if taxonomy_data:
            common_name = taxonomy_data.get("comName", common_name)
            scientific_name = taxonomy_data.get("sciName", "N/A")
        
        # Give eBird a tiny break
        time.sleep(RATE_LIMIT_DELAY)

        # 2. Extract genuine summary text via Wikipedia using scientific name
        general_knowledge = get_wikipedia_summary(scientific_name)
        
        # Fallback if Wikipedia summary isn't available for the specific scientific name
        if not general_knowledge:
            if scientific_name != "N/A":
                logger.warning(f"No Wikipedia article found for scientific name '{scientific_name}'. Trying common name '{common_name}'...")
            general_knowledge = get_wikipedia_summary(common_name)
            
            if not general_knowledge:
                general_knowledge = f"The {common_name} ({scientific_name}) is an observed bird species tracked globally under eBird code '{ebird_code}'."

        # 3. Consolidate into clean JSON payload matching your DB Schema
        record = {
            "ebird_code": ebird_code,
            "common_name": common_name,
            "general_knowledge": general_knowledge,
            "identification_tips": "",
            "habitat": "",
            "behaviour": "",
            "diet": "",
            "feeding_habits": ""
        }
        
        output_data.append(record)
        
        if idx % 20 == 0 or idx == total_species:
            logger.info(f"Progress: {idx}/{total_species} records processed.")
            # Incremental file backup so you don't lose progress if execution drops
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
        time.sleep(RATE_LIMIT_DELAY)

    logger.info(f"✓ Success! Generated {len(output_data)} completed records in '{args.output}'")

if __name__ == "__main__":
    main()