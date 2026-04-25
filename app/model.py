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
CUSTOM_MODEL_CLASSES_PATH = "singapore_bird_classes.txt"
RESNET_TEST_MODE = True

# ── ImageNet class labels (1000 classes) for EfficientNet-B0 ────────────────
_EFFICIENTNET_WEIGHTS = EfficientNet_B0_Weights.DEFAULT
IMAGENET_LABELS: list[str] = _EFFICIENTNET_WEIGHTS.meta["categories"]

# ── Preprocessing pipeline (same for both models — 224×224, ImageNet norm) ──
_PREPROCESS = transforms.Compose(
    [
        transforms.Resize(256),          # scale short edge to 256
        transforms.CenterCrop(224),      # crop to 224×224
        transforms.ToTensor(),           # HWC uint8 → CHW float32 [0,1]
        transforms.Normalize(            # ImageNet mean/std
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


class Prediction(NamedTuple):
    label: str
    confidence: float


# ── Custom ResNet50 Model Definition ───────────────────────────────────────
def load_resnet50(num_classes):
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Freeze backbone (optional but matches training)
    for param in model.parameters():
        param.requires_grad = False

    # Replace FC
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    return model


def _load_custom_model_classes() -> list[str]:
    """
    Load species class names from singapore_bird_classes.txt.
    Expected format: one species per line, in order (index 0 = class 0, etc).
    
    Falls back gracefully if file not found — uses placeholder labels.
    """
    try:
        if os.path.exists(CUSTOM_MODEL_CLASSES_PATH):
            with open(CUSTOM_MODEL_CLASSES_PATH, 'r') as f:
                classes = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(classes)} custom model classes from {CUSTOM_MODEL_CLASSES_PATH}")
            return classes
    except Exception as e:
        logger.warning(f"Could not load custom model classes: {e}")
    
    # Fallback: return None to signal that custom model is not properly configured
    return None


@lru_cache(maxsize=1)
def load_model() -> tuple[torch.nn.Module, list[str], torch.nn.Module | None, list[str] | None]:
    """
    Load model(s) based on configuration.
    
    Hybrid Mode (USE_HYBRID_MODE=true):
      Returns: (efficientnet_b0, imagenet_labels, resnet50, sg_species)
      Pipeline: EfficientNet bird_gate → ResNet50 species classification
    
    Legacy Mode (USE_HYBRID_MODE=false):
      Returns: (efficientnet_b0, imagenet_labels, None, None)
      Pipeline: EfficientNet → bird_gate → sg_filter (original)
    """
    logger.info("🎯 Loading EfficientNet-B0 for bird detection")
    efficientnet = efficientnet_b0(weights=_EFFICIENTNET_WEIGHTS)
    efficientnet.eval()
    logger.info("✅ EfficientNet-B0 loaded (bird_gate)")
    
    if USE_HYBRID_MODE:
        logger.info("🎯 Loading ResNet50 for SG species classification")
        
        sg_species = _load_custom_model_classes()
        if sg_species is None:
            raise RuntimeError(
                f"Hybrid mode enabled but {CUSTOM_MODEL_CLASSES_PATH} not found."
            )
        
        num_classes = len(sg_species)
        resnet = load_resnet50(num_classes)
        
        if not os.path.exists(CUSTOM_MODEL_PATH):
            raise RuntimeError(f"Model not found: {CUSTOM_MODEL_PATH}")
        
        state_dict = torch.load(CUSTOM_MODEL_PATH, map_location='cpu', weights_only=True)
        resnet.load_state_dict(state_dict)
        resnet.eval()
        
        logger.info("✅ ResNet50 loaded (%d SG species)", num_classes)
        return efficientnet, IMAGENET_LABELS, resnet, sg_species
    else:
        logger.info("ℹ️  Hybrid mode disabled (legacy EfficientNet-only pipeline)")
        return efficientnet, IMAGENET_LABELS, None, None


def preprocess(image_bytes: bytes) -> torch.Tensor:
    """Convert raw image bytes → normalised (1, 3, 224, 224) tensor."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _PREPROCESS(image)          # (3, 224, 224)
    return tensor.unsqueeze(0)           # (1, 3, 224, 224)


@torch.inference_mode()
def predict_top_k(image_bytes: bytes, k: int = 5) -> list[Prediction]:
    efficientnet, imagenet_labels, resnet, sg_species = load_model()
    tensor = preprocess(image_bytes)

    # 🚀 PURE RESNET TEST MODE
    if RESNET_TEST_MODE and resnet is not None:
        logits = resnet(tensor)
        probs = F.softmax(logits, dim=1).squeeze(0)

        k = min(k, probs.shape[0])  # prevent out-of-range
        top_probs, top_indices = torch.topk(probs, k)

        return [
            Prediction(
                label=sg_species[idx.item()],
                confidence=round(prob.item(), 4),
            )
            for prob, idx in zip(top_probs, top_indices)
        ]

    # 🧪 ORIGINAL PIPELINE (unused for now)
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