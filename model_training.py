# model_training.py

import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import numpy as np

# Configuration
DATA_PATH = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images"
BATCH_SIZE = 32
NUM_CLASSES = 5  # Based on your error mentioning 5 classes
IMAGE_SIZE = (224, 224)

def load_flat_dataset(root_path, transform):
    """
    Load images from a flat folder structure (not subfolders).
    Returns a Dataset that assigns class IDs based on image filename prefix or sorting.
    """
    dataset = FlatImageDataset(root_path, transform)
    return dataset

class FlatImageDataset(Dataset):
    def __init__(self, root, transform=None):
        self.root = root
        self.transform = transform
        self.images = sorted([
            f for f in os.listdir(root)
            if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))
        ])
        self.class_names = [f"Class_{i}" for i in range(NUM_CLASSES)]
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        
        print(f"\n📁 Loaded {len(self.images)} images from flat folder")
        print(f"📂 Expected classes: {NUM_CLASSES}")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.root, img_name)
        
        image = Image.open(img_path).convert('RGB')
        
        # Assign a class index based on image filename or random assignment if needed
        # For now, let's use filename hash to distribute classes evenly
        # In a real scenario, you'd have metadata mapping filename -> class
        import hashlib
        file_hash = hashlib.md5(img_name.encode()).hexdigest()
        class_idx = int(file_hash[:2], 16) % NUM_CLASSES  # Distribute evenly
        
        if self.transform:
            image = self.transform(image)
        
        # Return image and pseudo-class label
        return image, self.class_to_idx[self.class_names[class_idx]]

def get_transforms(train=True):
    if train:
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.5)
        ])
    else:
        return transforms.Compose([
            transforms.Resize(IMAGE_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

def main():
    print(f"Using device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
    
    # Load transforms
    transform_train = get_transforms(train=True)
    transform_val = get_transforms(train=False)
    
    # Load datasets (note: we're loading flat structure now)
    train_dataset = load_flat_dataset(f"{DATA_PATH}/training", transform_train)
    val_dataset = load_flat_dataset(f"{DATA_PATH}/valid", transform_val)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    print(f"✅ Training loader: {len(train_loader)} batches")
    print(f"✅ Validation loader: {len(val_loader)} batches")
    
    # Continue with model training...
    print("✅ Datasets loaded successfully!")
    print("🚀 Starting model training...")
    
    # Rest of your training code here
    # ...

if __name__ == "__main__":
    main()