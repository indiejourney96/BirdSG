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

def clear_existing_files(folder_path):
    """Safely clear existing files in a folder"""
    if os.path.exists(folder_path):
        try:
            files_to_delete = [f for f in os.listdir(folder_path) 
                              if os.path.isfile(os.path.join(folder_path, f))]
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
    print("🔄 Starting dataset split...")
    
    # 1. Create directories if they don't exist
    Path(TRAIN_DIR).mkdir(parents=True, exist_ok=True)
    Path(VALID_DIR).mkdir(parents=True, exist_ok=True)
    
    # 2. Clear existing files (THIS PREVENTS OVERWRITING!)
    clear_existing_files(TRAIN_DIR)
    clear_existing_files(VALID_DIR)
    
    # 3. Get all species folders
    species_dirs = [d for d in os.listdir(SOURCE_DIR) 
                    if os.path.isdir(os.path.join(SOURCE_DIR, d))]
    
    all_images = []
    # Collect all image paths
    for species in species_dirs:
        species_path = os.path.join(SOURCE_DIR, species)
        for img_file in os.listdir(species_path):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                img_path = os.path.join(species_path, img_file)
                all_images.append({
                    'path': img_path,
                    'filename': img_file,
                    'species': species
                })
    
    print(f"\n📊 Total images found: {len(all_images)}")
    
    if len(all_images) == 0:
        print("❌ No images found! Check your SOURCE_DIR path.")
        return
    
    # 4. Shuffle to ensure random split across species
    random.seed(42)  # For reproducibility
    random.shuffle(all_images)
    
    # 5. Split into train and val
    split_index = int(len(all_images) * TRAIN_RATIO)
    train_images = all_images[:split_index]
    val_images = all_images[split_index:]
    
    print(f"📊 Train images: {len(train_images)}")
    print(f"📊 Val images: {len(val_images)}")
    
    # 6. Copy images to training folder
    for img_info in train_images:
        src = img_info['path']
        dest = os.path.join(TRAIN_DIR, img_info['filename'])
        shutil.copy2(src, dest)
    
    # 7. Copy images to validation folder
    for img_info in val_images:
        src = img_info['path']
        dest = os.path.join(VALID_DIR, img_info['filename'])
        shutil.copy2(src, dest)
    
    # 8. Create species counts for verification
    train_species = {}
    val_species = {}
    
    for img_info in train_images:
        species = img_info['species']
        if species not in train_species:
            train_species[species] = 0
        train_species[species] += 1
        
    for img_info in val_images:
        species = img_info['species']
        if species not in val_species:
            val_species[species] = 0
        val_species[species] += 1
        
    print("\n✅ Training set distribution:")
    for species, count in sorted(train_species.items()):
        print(f"   {species}: {count} images")
    
    print("\n✅ Validation set distribution:")
    for species, count in sorted(val_species.items()):
        print(f"   {species}: {count} images")
    
    print("\n✨ Dataset split complete!")
    print(f"📁 Training folder: {TRAIN_DIR}")
    print(f"📁 Validation folder: {VALID_DIR}")

if __name__ == "__main__":
    split_dataset()