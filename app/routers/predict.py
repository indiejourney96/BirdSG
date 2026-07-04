"""
predict.py — Clean inference controller

Modes:
    - resnet_test  → pure ResNet evaluation (NO bird gate)
    - gate_test    → EfficientNet bird gate only
    - production   → full pipeline (EfficientNet → gate → ResNet → filter)
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.model import predict_top_k, load_model
from app.bird_gate import passes_bird_gate, BIRD_CONFIDENCE_THRESHOLD
from app.species_mapping import get_species, is_singapore_species
from app.database import build_sighting_storage_path, save_sighting, upload_sighting_image
from app.ebird import get_species_info
from app.species_mapping import get_species
from app.session_auth import get_authenticated_user_id

from collections import defaultdict
from time import time
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
MODE = os.getenv("MODE", "production")  # resnet_test | gate_test | production

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10

TOP_K_MODEL = 10
TOP_K_RETURN = 3

# ─────────────────────────────────────────────────────────────
# SIMPLE IN-MEMORY RATE LIMITER
# ─────────────────────────────────────────────────────────────
MAX_REQUESTS = 8
WINDOW_SECONDS = 60

request_history = defaultdict(list)


# ─────────────────────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────────────────────
class PredictionItem(BaseModel):
    label: str
    confidence: float
    singapore_match: bool



class PredictResponse(BaseModel):
    filename: str
    mode: str
    predictions: list[PredictionItem]
    singapore_filtered: bool
    sighting_id: str | None = None


# ─────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────
@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: Request,
    file: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
):
    user_id = get_authenticated_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

        # ─────────────────────────────────────────────
    # Simple IP-based rate limiter
    # 8 requests per 60 seconds
    # ─────────────────────────────────────────────
    client_ip = request.client.host if request.client else "unknown"
    now = time()

    # Remove requests older than the time window
    request_history[client_ip] = [
        t for t in request_history[client_ip]
        if now - t < WINDOW_SECONDS
    ]

    if len(request_history[client_ip]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute before trying again."
        )

    request_history[client_ip].append(now)
    
    # 1. Validate input
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'",
        )

    image_bytes = await file.read()

    if len(image_bytes) / (1024 * 1024) > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail="File too large")

    # 2. Run model (single call only)
    try:
        raw_results = predict_top_k(image_bytes, k=TOP_K_MODEL)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    top = raw_results[0]

    # ─────────────────────────────────────────────
    # MODE 1: RESNET TEST (NO BIRD GATE)
    # ─────────────────────────────────────────────
    if MODE == "resnet_test":
        predictions = raw_results[:TOP_K_RETURN]

    # ─────────────────────────────────────────────
    # MODE 2: BIRD GATE TEST (EfficientNet only)
    # ─────────────────────────────────────────────
    elif MODE == "gate_test":
        if not passes_bird_gate(top.label, top.confidence):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "No bird detected",
                },
            )
        predictions = raw_results[:TOP_K_RETURN]

    # ─────────────────────────────────────────────
    # MODE 3: PRODUCTION PIPELINE
    # ─────────────────────────────────────────────
    elif MODE == "production":
        try:
             # predict_top_k now does: EfficientNet gate + ResNet classification
            raw_results = predict_top_k(image_bytes, k=TOP_K_MODEL)
        except ValueError as exc:
             # Bird gate rejected it
            raise HTTPException(status_code=422, detail={"error": str(exc)})
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        predictions = raw_results[:TOP_K_RETURN]
    else:
        raise HTTPException(status_code=500, detail=f"Invalid MODE: {MODE}")

    # 3. Format output
    predictions_out = [
        PredictionItem(
            label=p.label,
            confidence=p.confidence,
            singapore_match=is_singapore_species(p.label),
        )
        for p in predictions
    ]

    try:
        storage_path, stored_filename, object_path = build_sighting_storage_path(
            file.filename or "bird.jpg",
            file.content_type,
        )
        upload_sighting_image(object_path, image_bytes, file.content_type)

        record = save_sighting(
            user_id=user_id,
            filename=stored_filename,
            storage_path=storage_path,
            predictions=[p.model_dump() for p in predictions_out],
            singapore_filtered=bool(
                any(p.singapore_match for p in predictions_out)
            ),
            lat=lat,
            lng=lng,
        )
        sighting_id = record.get("id")
    except Exception as exc:
            logger.error("Supabase sighting save failed: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to save sighting image")

    # 5. Response
    return PredictResponse(
        filename=file.filename,
        mode=MODE,
        predictions=predictions_out,
        singapore_filtered=any(p.singapore_match for p in predictions_out),
        sighting_id=sighting_id,
    )
