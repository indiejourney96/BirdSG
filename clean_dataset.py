#!/usr/bin/env python3
"""
🧹 BirdSG Data Cleaner CLI
Scans a dataset folder, detects blurry images, and asks for confirmation before deleting.
"""

import os
import sys
from pathlib import Path
import cv2
import time

# ---------------- FUNCTIONS ----------------

def detect_blur(image_path, threshold=100):
    """
    Detects blur using the variance of Laplacian method.
    Returns True if the image is considered blurry (needs deletion).
    """
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[Error] Could not read: {image_path}")
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # Variance of Laplacian
        variance = laplacian.var()
        
        # Threshold: 
        # High variance = Sharp (Keep)
        # Low variance = Blurry (Delete)
        is_blurry = variance < threshold
        
        return is_blurry, variance

    except Exception as e:
        print(f"[Error] Processing {image_path}: {e}")
        return False, 0

# ---------------- MAIN ----------------

def main():
    print("🚀 BirdSG Data Cleaner v1.0")
    print("-" * 40)
    
    # 1. Get User Input
    if len(sys.argv) < 2:
        print("❌ Please provide the dataset folder path.")
        print("Usage: python clean_dataset.py <dataset_folder>")
        sys.exit(1)

    dataset_folder = Path(sys.argv[1])

    if not dataset_folder.is_dir():
        print(f"❌ Folder not found: {dataset_folder}")
        sys.exit(1)

    # 2. Configuration
    # You can adjust this threshold if needed. 
    # 100 is a good starting point for JPEG photos.
    BLUR_THRESHOLD = 100
    
    # Counters
    total_images = 0
    flagged_images = 0
    
    print(f"\n📂 Scanning folder: {dataset_folder.absolute()}")
    print(f"⚠️  Blur Threshold: {BLUR_THRESHOLD}")
    print("-" * 40)

    # 3. Main Loop
    for root, dirs, files in os.walk(dataset_folder):
        for file in files:
            # Filter by extensions
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                total_images += 1
                file_path = os.path.join(root, file)
                
                # Progress bar logic
                if total_images % 10 == 0:
                    print(f"\n📍 Scanning image {total_images}...", file=sys.stderr)

                # Run detection
                is_blurry, score = detect_blur(file_path, BLUR_THRESHOLD)

                if is_blurry:
                    flagged_images += 1
                    
                    # Ask user
                    print(f"\n⚠️  Detected Blur Score: {score:.2f} (Below {BLUR_THRESHOLD})")
                    print(f"📁 File: {file_path}")
                    print(f"❓ Delete this image? (y/n/q)")
                    
                    response = input().strip().lower()

                    if response == 'y':
                        # Delete the file
                        os.remove(file_path)
                        print(f"✅ Deleted: {file_path}")
                    elif response == 'q':
                        print(f"\n⏸️  Quitting without deleting.")
                        print(f"📊 Stats: Processed {total_images} images. Found {flagged_images} blurry images.")
                        sys.exit(0)
                    elif response == 'n':
                        print(f"✅ Kept: {file_path}")
                    
                    # Press enter to continue
                    print("\n[Enter to continue]...")
                    input()
                    print("-" * 40)

    # 4. Final Summary
    print(f"\n\n🏁 Cleaning Complete!")
    print(f"Total Images Scanned: {total_images}")
    print(f"Flagged for Deletion: {flagged_images}")
    print("Remaining dataset is ready for training.")

if __name__ == "__main__":
    main()