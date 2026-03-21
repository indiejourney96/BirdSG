"""
model.py — EfficientNet-B0 inference module.

Responsible for:
  - Loading the pretrained model once at startup
  - Preprocessing uploaded image bytes
  - Running inference and returning top-k predictions
"""

from __future__ import annotations

import io
from functools import lru_cache
from typing import NamedTuple

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

# ── ImageNet class labels (1000 classes) bundled with torchvision ──────────
_WEIGHTS = EfficientNet_B0_Weights.DEFAULT
IMAGENET_LABELS: list[str] = _WEIGHTS.meta["categories"]

# ── Preprocessing pipeline (matches EfficientNet-B0 training config) ───────
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


@lru_cache(maxsize=1)
def load_model() -> torch.nn.Module:
    """
    Load EfficientNet-B0 with DEFAULT (ImageNet) weights.
    Called once at startup via lifespan; cached for all subsequent requests.
    """
    model = efficientnet_b0(weights=_WEIGHTS)
    model.eval()
    return model


def preprocess(image_bytes: bytes) -> torch.Tensor:
    """Convert raw image bytes → normalised (1, 3, 224, 224) tensor."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _PREPROCESS(image)          # (3, 224, 224)
    return tensor.unsqueeze(0)           # (1, 3, 224, 224)


@torch.inference_mode()
def predict_top_k(image_bytes: bytes, k: int = 5) -> list[Prediction]:
    """
    Run EfficientNet-B0 on image bytes and return top-k predictions.

    Args:
        image_bytes: Raw bytes of the uploaded image file.
        k:           Number of top predictions to return (default 5).

    Returns:
        List of Prediction(label, confidence) sorted by confidence desc.
    """
    model = load_model()
    tensor = preprocess(image_bytes)

    logits = model(tensor)                        # (1, 1000)
    probs = F.softmax(logits, dim=1).squeeze(0)   # (1000,)

    top_probs, top_indices = torch.topk(probs, k)

    return [
        Prediction(
            label=IMAGENET_LABELS[idx.item()],
            confidence=round(prob.item(), 4),
        )
        for prob, idx in zip(top_probs, top_indices)
    ]