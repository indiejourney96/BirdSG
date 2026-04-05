import os
import shutil
import random
from pathlib import Path

# Configuration
SOURCE_DIR = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\dataset"
TRAIN_DIR = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images\training"
VALID_DIR = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images\valid"
# Split ratio
TRAIN_RATIO = 0.7  # 70% for training

def clear_existing_folders(folder_path):
    """Safely clear existing image files in a folder (preserve species subfolders)"""
    if os.path.exists(folder_path):
        try:
            # List and remove only image files, not folders
            files_to_delete = [
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
                and os.path.splitext(f)[1].lower() in [
                    '.jpg', '.jpeg', '.png', '.bmp'
                ]
            ]
            if files_to_delete:
                print(f"\n🧹 Clearing {folder_path} ({len(files_to_delete)} files)...")
                for f in files_to_delete:
                    os.remove(os.path.join(folder_path, f))
                print(f"✅ Cleared {folder_path}")
            else:
                print(f"ℹ️ {folder_path} is empty or contains only folders")
        except Exception as e:
            print(f"⚠️ Error clearing {folder_path}: {e}")
        else:
            print(f"ℹ️ {folder_path} doesn't exist yet")

def split_dataset():
    print("🔄 Starting dataset split. ..")

    # 1. Create directories if they don't exist
    Path(TRAIN_DIR).mkdir(parents=True, exist_ok=True)
    Path(VALID_DIR).mkdir(parents=True, exist_ok=True)

    # 2. Clear existing files (THIS PREVENTS OVERWRITING!)
    clear_existing_folders(TRAIN_DIR)
    clear_existing_folders(VALID_DIR)

    # 3. Get all species folders
    species_dirs = [d for d in os.listdir(SOURCE_DIR)
                    if os.path.isdir(os.path.join(SOURCE_DIR, d))]

    print(f"\n📊 Found {len(species_dirs)} species in {SOURCE_DIR}")

    train_species_count = {}
    val_species_count = {}

    random.seed(42)

    # 4. For each species, collect and split images
    for species in species_dirs:
        species_path = os.path.join(SOURCE_DIR, species)
        species_images = []

        # Collect images for this species
        for img_file in os.listdir(species_path):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                img_path = os.path.join(species_path, img_file)
                species_images.append({
                    'path': img_path,
                    'filename': img_file,
                    'species': species
                })

        if not species_images:
            print(f"⚠️ No images found in species: {species}")
            continue

        print(f"\n📂 Processing species: {species} ({len(species_images)} images)")

        # 5. Shuffle this species' images
        random.seed(42)  # For reproducibility
        random.shuffle(species_images)

        # 6. Split into train and val for this species
        split_index = int(len(species_images) * TRAIN_RATIO)
        train_images = species_images[:split_index]
        val_images = species_images[split_index:]

        print(f"   Train: {len(train_images)}, Val: {len(val_images)}")

        # 7. Copy to training folder with species subfolder
        train_species_path = os.path.join(TRAIN_DIR, species)
        Path(train_species_path).mkdir(parents=True, exist_ok=True)

        for img_info in train_images:
            src = img_info['path']
            dest = os.path.join(train_species_path, img_info['filename'])
            shutil.copy2(src, dest)

        # 8. Copy to validation folder with species subfolder
        val_species_path = os.path.join(VALID_DIR, species)
        Path(val_species_path).mkdir(parents=True, exist_ok=True)

        for img_info in val_images:
            src = img_info['path']
            dest = os.path.join(val_species_path, img_info['filename'])
            shutil.copy2(src, dest)

        # 9. Track counts
        train_species_count[species] = len(train_images)
        val_species_count[species] = len(val_images)

    # 10. Print summary
    print("\n✅ Training set distribution:")
    for species, count in sorted(train_species_count.items()):
        print(f"   {species}: {count} images")

    print("\n✅ Validation set distribution:")
    for species, count in sorted(val_species_count.items()):
        print(f"   {species}: {count} images")

    print(f"\n✨ Dataset split complete!")
    print(f"📁 Training folder: {TRAIN_DIR}")
    print(f"📁 Validation folder: {VALID_DIR}")

if __name__ == "__main__":
    split_dataset()

