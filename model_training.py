# model_training.py

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms, models

# Configuration
DATA_PATH = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images"
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)
EPOCHS = 5


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


def get_model(num_classes, device):
    print("\n🔧 Loading pretrained ResNet50...")

    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Freeze backbone
    for param in model.parameters():
        param.requires_grad = False

    # Replace classifier
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    model = model.to(device)

    # Debug info
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"Total parameters: {total:,}")
    print(f"Trainable parameters: {trainable:,}")

    return model


def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()

    running_loss = 0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader, start=1):
        images = images.to(device)
        labels = labels.to(device)

        # 1️⃣ Reset gradients
        optimizer.zero_grad()
        print(f"\n[Batch {batch_idx}] Gradients reset")

        # 2️⃣ Forward pass
        outputs = model(images)
        print(f"[Batch {batch_idx}] Model outputs (logits) sample: {outputs[0].detach().cpu().numpy()}")

        # 3️⃣ Compute loss
        loss = criterion(outputs, labels)
        print(f"[Batch {batch_idx}] Batch loss: {loss.item():.4f}")

        # 4️⃣ Backpropagation
        loss.backward()
        print(f"[Batch {batch_idx}] Gradients computed (first param sample): {list(model.fc.parameters())[0].grad[0][0].item():.6f}")

        # 5️⃣ Update weights
        optimizer.step()
        print(f"[Batch {batch_idx}] Weights updated (first param sample): {list(model.fc.parameters())[0][0][0].item():.6f}")

        # 6️⃣ Track running loss
        running_loss += loss.item()

        # 7️⃣ Track accuracy
        _, predicted = torch.max(outputs, 1)
        batch_correct = (predicted == labels).sum().item()
        correct += batch_correct
        total += labels.size(0)
        batch_acc = 100 * batch_correct / labels.size(0)
        print(f"[Batch {batch_idx}] Batch accuracy: {batch_acc:.2f}%")

    # 8️⃣ Epoch-level metrics
    epoch_loss = running_loss / len(loader)
    epoch_acc = 100 * correct / total
    print(f"\n=== Epoch Summary ===")
    print(f"Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.2f}%")
    print("-" * 40)

    return epoch_loss, epoch_acc


def validate(model, loader, criterion, device):
    model.eval()

    running_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    accuracy = 100 * correct / total
    return running_loss / len(loader), accuracy


def main():
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Transforms
    transform_train = get_transforms(train=True)
    transform_val = get_transforms(train=False)

    # Dataset
    train_dataset = ImageFolder(f"{DATA_PATH}/training", transform=transform_train)
    val_dataset = ImageFolder(f"{DATA_PATH}/valid", transform=transform_val)

    print("\n📂 Detected classes:")
    for idx, class_name in enumerate(train_dataset.classes):
        print(f"   {idx}: {class_name}")

    num_classes = len(train_dataset.classes)
    print(f"\n🎯 Number of classes: {num_classes}")

    # DataLoader
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print(f"✅ Training loader: {len(train_loader)} batches")
    print(f"✅ Validation loader: {len(val_loader)} batches")

    # Model
    model = get_model(num_classes, device)

    # Loss
    criterion = nn.CrossEntropyLoss()

    # Optimizer (ONLY trainable params)
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=0.001
    )

    print("\n🚀 Starting training...\n")

    # Training loop
    for epoch in range(EPOCHS):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, optimizer, criterion, device
        )

        val_loss, val_acc = validate(
            model, val_loader, criterion, device
        )

        print(f"Epoch {epoch+1}/{EPOCHS}")
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"Val   Loss: {val_loss:.4f} | Val   Acc: {val_acc:.2f}%")
        print("-" * 40)


if __name__ == "__main__":
    main()