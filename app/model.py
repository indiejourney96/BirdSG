"""
model.py — Hybrid inference pipeline.

Hybrid Approach:
  1. EfficientNet-B0 → bird_gate (is it a bird?)
  2. Custom ResNet50 → SG species classification (no sg_filter needed)

Configuration:
  USE_HYBRID_MODE=true (default) — EfficientNet for bird detection + ResNet50 for species
  USE_HYBRID_MODE=false — Original pure EfficientNet-B0 pipeline
"""

from __future__ import annotations

import io
import logging
import os
from functools import lru_cache
from typing import NamedTuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms, models
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
USE_HYBRID_MODE = os.environ.get("USE_HYBRID_MODE", "true").lower() == "true"
CUSTOM_MODEL_PATH = "best_bird_model.pth"
RESNET_TEST_MODE = True  # direct ResNet inference (skip bird gate)

# ── EfficientNet (bird gate) ───────────────────────────────────────────────
_EFFICIENTNET_WEIGHTS = EfficientNet_B0_Weights.DEFAULT
IMAGENET_LABELS: list[str] = _EFFICIENTNET_WEIGHTS.meta["categories"]

# ── Preprocessing ──────────────────────────────────────────────────────────
_PREPROCESS = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


class Prediction(NamedTuple):
    label: str
    confidence: float


# ── ResNet50 Builder (Dynamic) ─────────────────────────────────────────────
def build_resnet50(num_classes: int) -> nn.Module:
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Freeze backbone (same as training)
    for param in model.parameters():
        param.requires_grad = False

    # Replace classification head
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    return model


# ── Model Loader (Portable + Robust) ───────────────────────────────────────
@lru_cache(maxsize=1)
def load_model() -> tuple[
    nn.Module,
    list[str],
    nn.Module | None,
    list[str] | None
]:
    """
    Returns:
        (efficientnet, imagenet_labels, resnet, class_names)

    Hybrid Mode:
        EfficientNet → bird detection
        ResNet50     → species classification

    Portable Design:
        - Classes are loaded from checkpoint
        - No external files required
    """

    # ── Load EfficientNet ────────────────────────────────────────────────
    logger.info("🎯 Loading EfficientNet-B0 (bird gate)")
    efficientnet = efficientnet_b0(weights=_EFFICIENTNET_WEIGHTS)
    efficientnet.eval()
    logger.info("✅ EfficientNet ready")

    if not USE_HYBRID_MODE:
        logger.info("ℹ️ Hybrid mode disabled")
        return efficientnet, IMAGENET_LABELS, None, None

    # ── Load Custom ResNet ───────────────────────────────────────────────
    logger.info("🎯 Loading ResNet50 (species classifier)")

    if not os.path.exists(CUSTOM_MODEL_PATH):
        raise RuntimeError(f"❌ Model not found: {CUSTOM_MODEL_PATH}")

    checkpoint = torch.load(CUSTOM_MODEL_PATH, map_location="cpu")

    # ✅ Preferred format (portable)
    if "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
        class_names = checkpoint.get("classes", None)
    else:
        # ⚠️ Legacy fallback (not portable)
        logger.warning("⚠️ Legacy checkpoint detected (no class labels inside)")
        state_dict = checkpoint
        class_names = None

    if class_names is None:
        raise RuntimeError(
            "❌ Checkpoint does not contain class labels.\n"
            "Please retrain model using:\n"
            "torch.save({'model_state_dict': ..., 'classes': [...]})"
        )

    num_classes = len(class_names)

    # Build correct architecture dynamically
    resnet = build_resnet50(num_classes)

    # Load weights
    resnet.load_state_dict(state_dict)
    resnet.eval()

    logger.info(f"✅ ResNet50 ready ({num_classes} classes)")

    return efficientnet, IMAGENET_LABELS, resnet, class_names


# ── Image Preprocessing ────────────────────────────────────────────────────
def preprocess(image_bytes: bytes) -> torch.Tensor:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _PREPROCESS(image)
    return tensor.unsqueeze(0)  # (1, 3, 224, 224)


# ── Inference ──────────────────────────────────────────────────────────────
@torch.inference_mode()
def predict_top_k(image_bytes: bytes, k: int = 5) -> list[Prediction]:
    efficientnet, imagenet_labels, resnet, class_names = load_model()
    tensor = preprocess(image_bytes)

    # 🚀 Direct ResNet Mode (recommended for your use case)
    if RESNET_TEST_MODE and resnet is not None:
        logits = resnet(tensor)
        probs = F.softmax(logits, dim=1).squeeze(0)

        k = min(k, probs.shape[0])
        top_probs, top_indices = torch.topk(probs, k)

        return [
            Prediction(
                label=class_names[idx.item()],
                confidence=round(prob.item(), 4),
            )
            for prob, idx in zip(top_probs, top_indices)
        ]

    # 🧪 Hybrid Mode (EfficientNet → bird filtering)
    logits = efficientnet(tensor)
    probs = F.softmax(logits, dim=1).squeeze(0)
    top_probs, top_indices = torch.topk(probs, k)

    return [
        Prediction(
            label=imagenet_labels[idx.item()],
            confidence=round(prob.item(), 4),
        )
        for prob, idx in zip(top_probs, top_indices)
    ]