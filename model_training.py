# model_training.py

import os
import torch
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms

# Configuration
DATA_PATH = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images"
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)


def get_transforms(train=True):
    if train:
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.5)
        ])
    else:
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])


def main():
    # 1. Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Transforms
    transform_train = get_transforms(train=True)
    transform_val = get_transforms(train=False)

    # 3. Load dataset (folder-based labels)
    train_dataset = ImageFolder(f"{DATA_PATH}/training", transform=transform_train)
    val_dataset = ImageFolder(f"{DATA_PATH}/valid", transform=transform_val)

    # 4. Print detected classes
    print("\n📂 Detected classes:")
    for idx, class_name in enumerate(train_dataset.classes):
        print(f"   {idx}: {class_name}")

    num_classes = len(train_dataset.classes)
    print(f"\n🎯 Number of classes: {num_classes}")

    # 5. DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    print(f"✅ Training loader: {len(train_loader)} batches")
    print(f"✅ Validation loader: {len(val_loader)} batches")

    print("✅ Datasets loaded successfully!")
    print("🚀 Ready for model training...")


if __name__ == "__main__":
    main()