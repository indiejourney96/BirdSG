#!/usr/bin/env python3
"""
🧹 BirdSG Data Cleaner CLI v2.1 — with bird detection
Batch-scans dataset folder, detects images without birds + blurry images + duplicates, auto-deletes in batch mode.
Usage:
  python clean_dataset.py dataset                          # interactive (original)
  python clean_dataset.py dataset --batch                  # auto-delete all flagged images
  python clean_dataset.py dataset --preview                # just show stats, don't delete
  python clean_dataset.py dataset --threshold=150          # adjust blur sensitivity
  python clean_dataset.py dataset --bird-confidence=0.10   # adjust bird detection confidence
  python clean_dataset.py dataset --no-bird-check          # skip bird detection (faster)
"""

import os
import re
import sys
from pathlib import Path

import cv2
import hashlib

import torch
import torch.nn.functional as F
from torchvision import transforms, models
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
from PIL import Image

from app.bird_gate import IMAGENET_BIRD_CLASSES

# ---------------- BIRD DETECTION ----------------

_IMAGENET_LABELS = EfficientNet_B0_Weights.DEFAULT.meta["categories"]

_bird_device = None
_bird_model = None
_bird_preprocess = None


def _get_device():
    """Detect best available device: DirectML (AMD) → CPU."""
    try:
        import torch_directml
        device = torch_directml.device()
        print("🚀 Using AMD GPU via DirectML")
        return device
    except ImportError:
        print("⚠️ torch-directml not installed, falling back to CPU")
        return torch.device("cpu")


def _load_bird_detector():
    """Lazy-load EfficientNet-B0 once (cached across all images)."""
    global _bird_model, _bird_preprocess, _bird_device
    if _bird_model is not None:
        return

    _bird_device = _get_device()
    print("🔧 Loading EfficientNet-B0 for bird detection...")
    _bird_model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    _bird_model.eval()
    _bird_model.to(_bird_device)

    _bird_preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])
    print("✅ Bird detector ready")


def detect_bird(image_path, confidence_threshold=0.10):
    """
    Check if image contains a bird using EfficientNet-B0 + ImageNet bird classes.

    Returns (is_bird: bool, label: str, confidence: float).
    On error, returns (True, "", 0.0) to avoid false deletions from model failures.
    """
    try:
        _load_bird_detector()

        image = Image.open(image_path).convert("RGB")
        tensor = _bird_preprocess(image).unsqueeze(0).to(_bird_device)

        with torch.no_grad():
            logits = _bird_model(tensor)
            probs = F.softmax(logits, dim=1).squeeze(0)
            top_prob, top_idx = torch.max(probs, dim=0)
            label = _IMAGENET_LABELS[top_idx.item()]

        normalised = label.lower().strip()
        label_is_bird = (
            normalised in IMAGENET_BIRD_CLASSES
            or any(
                bird in normalised or normalised in bird
                for bird in IMAGENET_BIRD_CLASSES
            )
        )
        is_bird = label_is_bird and top_prob.item() >= confidence_threshold

        return is_bird, label, round(top_prob.item(), 4)

    except Exception as e:
        print(f"[Error] Bird detection failed for {image_path}: {e}")
        return True, "", 0.0


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
            return False, 0
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance < threshold, variance

    except Exception as e:
        print(f"[Error] Processing {image_path}: {e}")
        return False, 0


def file_hash(image_path):
    """Return SHA256 hash of file contents (efficient for duplicate detection)."""
    try:
        h = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# ---------------- MAIN ----------------

def main():
    print("🚀 BirdSG Data Cleaner v2.1 — with bird detection")
    print("-" * 40)

    # Parse args
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]

    if not args:
        print("❌ Please provide the dataset folder path.")
        print("Usage: python clean_dataset.py <dataset_folder> [--batch] [--preview] [--threshold=N] [--bird-confidence=N] [--no-bird-check]")
        sys.exit(1)

    dataset_folder = Path(args[0])
    if not dataset_folder.is_dir():
        print(f"❌ Folder not found: {dataset_folder}")
        sys.exit(1)

    batch_mode = '--batch' in flags
    preview_mode = '--preview' in flags
    no_bird_check = '--no-bird-check' in flags
    BLUR_THRESHOLD = 60
    BIRD_CONFIDENCE = 0.10
    for f in flags:
        if f.startswith('--threshold='):
            try:
                BLUR_THRESHOLD = int(f.split('=')[1])
            except ValueError:
                pass
        if f.startswith('--bird-confidence='):
            try:
                BIRD_CONFIDENCE = float(f.split('=')[1])
            except ValueError:
                pass

    total_images = 0
    flagged_blurry = 0
    flagged_duplicates = 0
    flagged_no_bird = 0
    deleted_count = 0
    seen_hashes = {}

    if batch_mode:
        print("⚡ Running in BATCH mode — will auto-delete flagged images")
    elif preview_mode:
        print("🔍 PREVIEW mode — showing stats, no files will be deleted")
    else:
        print("💬 Interactive mode — you'll be prompted per image")
    print(f"📂 Folder: {dataset_folder.absolute()}")
    print(f"⚠️  Blur Threshold: {BLUR_THRESHOLD}")
    if not no_bird_check:
        print(f"🐦 Bird Confidence Threshold: {BIRD_CONFIDENCE}")
    else:
        print("🐦 Bird detection: DISABLED")
    print("-" * 40)

    # Collect all image paths first
    image_files = []
    for root, dirs, files in os.walk(dataset_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                image_files.append(os.path.join(root, file))

    image_files.sort(key=lambda p: int(re.search(r'(\d+)', os.path.basename(p)).group(1)))
    total = len(image_files)
    print(f"📸 Found {total} images\n")

    for idx, file_path in enumerate(image_files, 1):
        if idx % 20 == 0 or idx == total:
            print(f"  Progress: {idx}/{total}", flush=True)

        reasons = []

        # 1. Bird check (most expensive, done first)
        if not no_bird_check:
            has_bird, bird_label, bird_conf = detect_bird(file_path, BIRD_CONFIDENCE)
            if not has_bird:
                reasons.append(f"no bird ({bird_label}, conf={bird_conf})")
                flagged_no_bird += 1

        # 2. Blur check
        is_blurry, score = detect_blur(file_path, BLUR_THRESHOLD)
        if is_blurry:
            reasons.append(f"blurry (score={score:.1f})")
            flagged_blurry += 1

        # 3. Duplicate check
        fhash = file_hash(file_path)
        if fhash:
            if fhash in seen_hashes:
                reasons.append(f"duplicate of {seen_hashes[fhash]}")
                flagged_duplicates += 1
            else:
                seen_hashes[fhash] = file_path

        if reasons:
            reason_str = ", ".join(reasons)

            if preview_mode:
                print(f"  ⚠️  Would delete: {file_path} [{reason_str}]")
                continue

            if batch_mode:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"  🗑️  Deleted: {file_path} [{reason_str}]")
                except Exception as e:
                    print(f"  ❌ Failed to delete {file_path}: {e}")
                continue

            # Interactive mode
            print(f"\n⚠️  Issue: {reason_str}")
            print(f"📁 File: {file_path}")
            print(f"❓ Delete this image? (y/n/q)", end=" ")
            response = input().strip().lower()
            if response == 'y':
                os.remove(file_path)
                deleted_count += 1
                print(f"✅ Deleted")
            elif response == 'q':
                print(f"\n⏸️  Quitting.")
                break
            else:
                print(f"✅ Kept")

    # Summary
    print("\n" + "=" * 40)
    print(f"🏁 Cleaning Complete!")
    print(f"Total images scanned: {total}")
    print(f"No bird detected: {flagged_no_bird}")
    print(f"Blurry images flagged: {flagged_blurry}")
    print(f"Duplicates flagged: {flagged_duplicates}")
    print(f"Total deleted: {deleted_count}")
    print(f"Remaining: {total - deleted_count}")
    print("=" * 40)

if __name__ == "__main__":
    main()