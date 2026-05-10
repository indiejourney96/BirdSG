# model_training.py

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms, models

from sklearn.metrics import confusion_matrix, classification_report
import numpy as np

# Configuration
DATA_PATH = r"C:\Users\Admin\Daryl\SD Projects\BirdSG\data\images"
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)
EPOCHS = 10


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
            transforms.RandomErasing(p=0.2)
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

    for param in model.parameters():
        param.requires_grad = False

    # Unfreeze layer4
    for param in model.layer4.parameters():
        param.requires_grad = True

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


def validate(model, loader, criterion, device, return_preds=False):
    model.eval()

    running_loss = 0
    correct = 0
    total = 0

    all_preds = []
    all_labels = []

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

            if return_preds:
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

    accuracy = 100 * correct / total

    if return_preds:
        return running_loss / len(loader), accuracy, all_labels, all_preds

    return running_loss / len(loader), accuracy


def main():
    # Device
    try:
        import torch_directml

        device = torch_directml.device()
        print("🚀 Using AMD GPU via DirectML")

    except ImportError:
        device = torch.device("cpu")
        print("⚠️ torch-directml not installed, falling back to CPU")

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

    # Optimizer
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=0.001
    )

    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='max',      # maximize validation accuracy
        patience=3,
        factor=0.5,
        verbose=True
    )

    # Early stopping + best model tracking
    best_val_acc = 0
    best_model_path = "best_bird_model.pth"
    no_improve_epochs = 0
    early_stop_patience = 5

    print("\n🚀 Starting training...\n")

    for epoch in range(EPOCHS):
        print(f"\n========== Epoch {epoch+1}/{EPOCHS} ==========")

        # ---- Train ----
        train_loss, train_acc = train_one_epoch(
            model, train_loader, optimizer, criterion, device
        )

        # ---- Validate ----
        val_loss, val_acc, labels, preds = validate(model, val_loader, criterion, device, return_preds=True)

        # ---- Confusion Matrix ----
        cm = confusion_matrix(labels, preds)
        print("\n========== Confusion Matrix ==========")
        print(cm)

        # ---- Precision / Recall / F1 ----
        print("\n========== Classification Report ==========")

        class_names = train_dataset.classes

        report = classification_report(
            labels,
            preds,
            target_names=class_names,
            digits=4,
            zero_division=0
        )

        print(report)

        # ---- Scheduler step ----
        scheduler.step(val_acc)

        # ---- Print learning rate ----
        current_lr = optimizer.param_groups[0]['lr']
        print(f"📉 Current Learning Rate: {current_lr:.6f}")

        # ---- Best model saving ----
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            no_improve_epochs = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "classes": train_dataset.classes
            }, "best_bird_model.pth")
            print(f"💾 New best model saved! Val Acc: {val_acc:.2f}%")
        else:
            no_improve_epochs += 1
            print(f"⚠️ No improvement for {no_improve_epochs} epoch(s)")

        # ---- Epoch summary ----
        print("\nEpoch Summary")
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"Val   Loss: {val_loss:.4f} | Val   Acc: {val_acc:.2f}%")
        print(f"Best  Val Acc so far: {best_val_acc:.2f}%")
        print("-" * 40)

        # ---- Early stopping ----
        if no_improve_epochs >= early_stop_patience:
            print("⏹ Early stopping triggered")
            break

    print("\n🏁 Training finished")
    print(f"Best model saved at: {best_model_path}")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")


if __name__ == "__main__":
    main()