"""
batch_download_bird_photos.py

Download bird photos from Wikimedia Commons and store in Supabase Storage.

Usage:
    # Download and upload all 400 birds
    python scripts/batch_download_bird_photos.py --all

    # Download only top 20 common birds (MVP quick win)
    python scripts/batch_download_bird_photos.py --limit 20

    # Resume from where you left off
    python scripts/batch_download_bird_photos.py --resume

    # Check what's been uploaded
    python scripts/batch_download_bird_photos.py --validate
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.species_mapping import SPECIES_MAP
from app.wikimedia import get_wikimedia_photo
from app.database import supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BUCKET_NAME = "bird-photos"
RATE_LIMIT_DELAY = 0.5  # seconds between Wikimedia requests

# Top 20 most common Singapore birds (for MVP quick win)
TOP_20_COMMON = [
    "yellow_vented_bulbul",
    "asian_koel",
    "black_crested_bulbul",
    "spotted_dove",
    "common_kingfisher",
    "common_hill_myna",
    "house_crow",
    "asian_glossy_starling",
    "pacific_swallow",
    "oriental_magpie_robin",
    "white_rumped_shama",
    "asian_house_martin",
    "baya_weaver",
    "zebra_dove",
    "straw_headed_bulbul",
    "blue_throated_bee_eater",
    "dollarbird",
    "barn_swallow",
    "little_egret",
    "great_egret",
]


def ensure_bucket_exists() -> None:
    """Create bird-photos bucket if it doesn't exist."""
    try:
        supabase.storage.create_bucket(BUCKET_NAME, options={"public": True})
        logger.info("Created bucket: %s", BUCKET_NAME)
    except Exception as e:
        if "already exists" in str(e):
            logger.info("Bucket already exists: %s", BUCKET_NAME)
        else:
            logger.error("Failed to create bucket: %s", e)
            raise


def download_photo_from_wikimedia(
    species_name: str,
    ebird_code: str,
) -> Optional[tuple[bytes, str]]:
    """
    Download photo from Wikimedia Commons.

    Returns:
        (photo_bytes, filename) or None if not found/failed.
    """
    try:
        photo_info = get_wikimedia_photo(species_name)
        if not photo_info or not photo_info.get("url"):
            logger.debug("No photo found on Wikimedia for: %s", species_name)
            return None

        photo_url = photo_info["url"]
        logger.debug("Downloading from: %s", photo_url)

        headers = {
            "User-Agent": "BirdSGApp/1.0 (daryl@hotmail.com) httpx/0.27.0"
        }

        resp = httpx.get(photo_url, headers=headers, timeout=10)
        resp.raise_for_status()

        # Generate filename
        filename = f"{ebird_code}.jpg"

        return resp.content, filename

    except Exception as e:
        logger.warning("Failed to download photo for %s: %s", species_name, e)
        return None


def upload_photo_to_supabase(
    photo_bytes: bytes,
    filename: str,
) -> Optional[str]:
    """
    Upload photo to Supabase Storage.

    Returns:
        Public URL if successful, None if failed.
    """
    try:
        response = supabase.storage.from_(BUCKET_NAME).upload(
            filename,
            photo_bytes,
            file_options={
                "content-type": "image/jpeg",
                "upsert": "true"  # FIXED: This allows overwriting existing files
            },
        )
        logger.debug("Uploaded to Supabase: %s", filename)

        # Get public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)
        return public_url

    except Exception as e:
        logger.warning("Failed to upload %s: %s", filename, e)
        return None


def update_bird_details_photo_url(
    ebird_code: str,
    photo_url: str,
) -> None:
    """Update bird_species_details table with photo URL."""
    try:
        supabase.table("bird_species_details").update(
            {
                "photo_url": photo_url,
                "photo_source": "local",
            }
        ).eq("ebird_code", ebird_code).execute()

        logger.debug("Updated bird_species_details for %s", ebird_code)

    except Exception as e:
        logger.warning("Failed to update bird_species_details for %s: %s", ebird_code, e)


def load_progress() -> set:
    """Load previously downloaded species from progress file."""
    progress_file = Path("photo_download_progress.json")
    if progress_file.exists():
        try:
            with open(progress_file, "r") as f:
                data = json.load(f)
                return set(data.get("completed", []))
        except Exception as e:
            logger.warning("Failed to load progress: %s", e)
    return set()


def save_progress(completed: set) -> None:
    """Save progress to file for resuming."""
    progress_file = Path("photo_download_progress.json")
    try:
        with open(progress_file, "w") as f:
            json.dump({"completed": list(completed)}, f)
    except Exception as e:
        logger.warning("Failed to save progress: %s", e)


def batch_download(limit: Optional[int] = None, resume: bool = False) -> None:
    """
    Download and upload bird photos in batch.

    Args:
        limit: Download only first N species (None = all)
        resume: Skip already downloaded species
    """
    logger.info("Starting batch photo download...")

    ensure_bucket_exists()

    # Determine which birds to download
    if limit == 20:
        species_to_download = {k: SPECIES_MAP[k] for k in TOP_20_COMMON if k in SPECIES_MAP}
        logger.info("Downloading top 20 common birds only")
    else:
        species_to_download = SPECIES_MAP
        if limit:
            species_to_download = dict(list(species_to_download.items())[:limit])
            logger.info("Downloading first %d birds", limit)

    # Load progress if resuming
    completed = load_progress() if resume else set()

    total = len(species_to_download)
    success = 0
    failed = 0
    skipped = len(completed)

    logger.info("Total species to process: %d (skipped: %d)", total, skipped)

    for idx, (label, info) in enumerate(species_to_download.items(), 1):
        if resume and label in completed:
            logger.debug("[%d/%d] SKIPPED (already downloaded): %s", idx, total, label)
            continue

        common_name = info.get("common_name")
        ebird_code = info.get("ebird_code")

        logger.info("[%d/%d] Processing: %s", idx, total, common_name)

        try:
            # Download from Wikimedia
            result = download_photo_from_wikimedia(common_name, ebird_code)
            if not result:
                logger.warning("No photo found for: %s", common_name)
                failed += 1
                completed.add(label)
                save_progress(completed)
                time.sleep(RATE_LIMIT_DELAY)
                continue

            photo_bytes, filename = result

            # Upload to Supabase
            public_url = upload_photo_to_supabase(photo_bytes, filename)
            if not public_url:
                logger.warning("Upload failed for: %s", common_name)
                failed += 1
                completed.add(label)
                save_progress(completed)
                time.sleep(RATE_LIMIT_DELAY)
                continue

            # Update database
            update_bird_details_photo_url(ebird_code, public_url)

            success += 1
            completed.add(label)
            save_progress(completed)

            logger.info("✓ Success: %s", common_name)

        except Exception as e:
            logger.error("Error processing %s: %s", common_name, e)
            failed += 1

        time.sleep(RATE_LIMIT_DELAY)

    logger.info("\n" + "=" * 60)
    logger.info("Batch download complete:")
    logger.info("  Success: %d", success)
    logger.info("  Failed: %d", failed)
    logger.info("  Skipped: %d", skipped)
    logger.info("  Total: %d/%d", success + skipped, total)
    logger.info("=" * 60)


def validate_uploads() -> None:
    """Check what photos have been uploaded to Supabase."""
    try:
        logger.info("Validating uploaded photos...")

        # List all files in bucket
        files = supabase.storage.from_(BUCKET_NAME).list()

        logger.info("Total photos in storage: %d", len(files))

        # Check which species have photos
        species_with_photos = set()
        for file in files:
            ebird_code = file["name"].replace(".jpg", "")
            species_with_photos.add(ebird_code)

        # Calculate coverage
        total_species = len(SPECIES_MAP)
        coverage = len(species_with_photos) / total_species * 100

        logger.info("Coverage: %d/%d (%.1f%%)", len(species_with_photos), total_species, coverage)

        # Find missing
        missing = []
        for label, info in SPECIES_MAP.items():
            ebird_code = info.get("ebird_code")
            if ebird_code not in species_with_photos:
                missing.append(label)

        if missing:
            logger.info("Missing photos for: %d species", len(missing))
            if len(missing) <= 10:
                for label in missing[:10]:
                    logger.info("  - %s", label)

    except Exception as e:
        logger.error("Validation failed: %s", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch download and upload bird photos to Supabase Storage"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all 400 birds (takes ~20 min)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Download only first N birds (e.g., --limit 20 for MVP)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last completed bird (skip already downloaded)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Check what photos are already uploaded",
    )

    args = parser.parse_args()

    if args.validate:
        validate_uploads()
    elif args.all:
        batch_download(limit=None, resume=args.resume)
    elif args.limit:
        batch_download(limit=args.limit, resume=args.resume)
    else:
        parser.print_help()
