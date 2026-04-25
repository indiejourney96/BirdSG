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

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.model import predict_top_k, load_model
from app.bird_gate import passes_bird_gate, BIRD_CONFIDENCE_THRESHOLD
from app.sg_filter import is_singapore_species
from app.database import save_sighting
from app.ebird import get_species_info
from app.imagenet_to_ebird import get_ebird_code
from app.xeno_canto import get_reference_audio

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
MODE = os.getenv("MODE", "resnet_test")  # resnet_test | gate_test | production

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10

TOP_K_MODEL = 10
TOP_K_RETURN = 3


# ─────────────────────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────────────────────
class PredictionItem(BaseModel):
    label: str
    confidence: float
    singapore_match: bool


class RecordingInfo(BaseModel):
    audio_url: str | None
    recording_id: str | None
    recordist: str | None
    location: str | None


class PredictResponse(BaseModel):
    filename: str
    mode: str
    predictions: list[PredictionItem]
    singapore_filtered: bool
    sighting_id: str | None = None
    recording: RecordingInfo | None = None


# ─────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────
@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
):
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
                    "top_prediction": top.label,
                    "confidence": top.confidence,
                    "threshold": BIRD_CONFIDENCE_THRESHOLD,
                },
            )
        predictions = raw_results[:TOP_K_RETURN]

    # ─────────────────────────────────────────────
    # MODE 3: PRODUCTION PIPELINE
    # ─────────────────────────────────────────────
    elif MODE == "production":
        if not passes_bird_gate(top.label, top.confidence):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "No bird detected",
                    "top_prediction": top.label,
                    "confidence": top.confidence,
                    "threshold": BIRD_CONFIDENCE_THRESHOLD,
                },
            )

        sg_matches = [r for r in raw_results if is_singapore_species(r.label)]
        predictions = sg_matches[:TOP_K_RETURN] if sg_matches else raw_results[:1]

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

    # 4. Optional: enrichment (only for production)
    recording = None
    sighting_id = None

    if MODE == "production":
        try:
            top_label = predictions_out[0].label
            ebird_code = get_ebird_code(top_label)
            species_info = get_species_info(ebird_code) if ebird_code else None
            species_name = species_info.get("common_name") if species_info else top_label

            xc = get_reference_audio(species_name)
            if xc:
                recording = RecordingInfo(**xc)
        except Exception as exc:
            logger.error("Xeno-canto fetch failed: %s", exc)

        try:
            record = save_sighting(
                filename=file.filename,
                predictions=[p.model_dump() for p in predictions_out],
                singapore_filtered=bool(
                    any(p.singapore_match for p in predictions_out)
                ),
                lat=lat,
                lng=lng,
            )
            sighting_id = record.get("id")
        except Exception as exc:
            logger.error("Supabase write failed: %s", exc)

    # 5. Response
    return PredictResponse(
        filename=file.filename,
        mode=MODE,
        predictions=predictions_out,
        singapore_filtered=any(p.singapore_match for p in predictions_out),
        sighting_id=sighting_id,
        recording=recording,
    )