"""
bulk_insert_bird_details.py

Utility script to bulk-insert bird species details into the bird_species_details
table. Reads from a JSON file and inserts into Supabase.

Usage:
    python scripts/bulk_insert_bird_details.py --file bird_details.json

Structure of bird_details.json:
    [
      {
        "ebird_code": "tufduc",
        "common_name": "Tufted Duck",
        "general_knowledge": "...",
        "identification_tips": "...",
        "habitat": "...",
        "behaviour": "...",
        "diet": "...",
        "feeding_habits": "..."
      },
      ...
    ]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bulk_insert(json_file: str) -> None:
    """Load bird details from JSON and insert into Supabase."""
    file_path = Path(json_file)
    if not file_path.exists():
        logger.error("File not found: %s", json_file)
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", e)
        return

    if not isinstance(data, list):
        logger.error("Expected a list of records in JSON")
        return
    inserted = 0
    skipped = 0

    for record in data:
        required_fields = {"ebird_code", "common_name"}
        if not required_fields.issubset(record.keys()):
            logger.warning("Skipping record missing required fields: %s", record)
            skipped += 1
            continue

        try:
            response = supabase.table("bird_species_details").upsert(
                record, on_conflict="ebird_code"
            ).execute()

            inserted += 1
            logger.info(
                "Inserted/updated: %s (%s)",
                record.get("common_name"),
                record.get("ebird_code"),
            )

        except Exception as e:
            logger.error("Failed to insert %s: %s", record.get("ebird_code"), e)
            skipped += 1

    logger.info(
        "Bulk insert complete: %d inserted/updated, %d skipped",
        inserted,
        skipped,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bulk insert bird details into Supabase"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON file with bird details",
    )
    args = parser.parse_args()
    bulk_insert(args.file)