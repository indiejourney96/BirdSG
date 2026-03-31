"""
predict.py — POST /predict endpoint.

Pipeline:
    1. Validate file type and size
    2. Run EfficientNet-B0 inference (top 10)
    3. Bird gate — reject non-bird images
    4. Singapore filter — keep local species matches
    5. Fetch Xeno-canto reference recording for top match
    6. Persist to Supabase (failures are logged, never raised)
    7. Return response
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.bird_gate import BIRD_CONFIDENCE_THRESHOLD, passes_bird_gate
from app.database import save_sighting
from app.ebird import get_species_info
from app.imagenet_to_ebird import get_ebird_code
from app.model import predict_top_k
from app.sg_filter import is_singapore_species
from app.xeno_canto import get_reference_audio

logger = logging.getLogger(__name__)

ALLOWED_TYPES    = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
TOP_K_MODEL      = 10
TOP_K_RETURN     = 3

router = APIRouter()


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
    predictions: list[PredictionItem]
    singapore_filtered: bool
    sighting_id: str | None = None
    recording: RecordingInfo | None = None   # Xeno-canto reference audio for top match


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
):
    # 1. Validate
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {sorted(ALLOWED_TYPES)}",
        )

    image_bytes = await file.read()
    if len(image_bytes) / (1024 * 1024) > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")

    # 2. Inference
    try:
        raw_results = predict_top_k(image_bytes, k=TOP_K_MODEL)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not process image: {exc}")

    # 3. Bird gate
    top = raw_results[0]
    if not passes_bird_gate(top.label, top.confidence):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "No bird detected",
                "message": "Please upload a clear photo of a bird.",
                "top_prediction": top.label,
                "confidence": top.confidence,
                "threshold": BIRD_CONFIDENCE_THRESHOLD,
            },
        )

    # 4. Singapore filter
    sg_matches = [r for r in raw_results if is_singapore_species(r.label)]
    final    = sg_matches[:TOP_K_RETURN] if sg_matches else raw_results[:1]
    filtered = bool(sg_matches)

    predictions_out = [
        PredictionItem(
            label=r.label,
            confidence=r.confidence,
            singapore_match=is_singapore_species(r.label),
        )
        for r in final
    ]

    # 5. Fetch Xeno-canto reference recording for the top prediction
    recording: RecordingInfo | None = None
    try:
        top_label     = predictions_out[0].label
        ebird_code    = get_ebird_code(top_label)
        species_info  = get_species_info(ebird_code) if ebird_code else None
        species_name  = species_info.get("common_name") if species_info else top_label
        xc            = get_reference_audio(species_name)
        if xc:
            recording = RecordingInfo(**xc)
    except Exception as exc:
        logger.error("Xeno-canto fetch failed: %s", exc)

    # 6. Persist to Supabase
    sighting_id: str | None = None
    try:
        record = save_sighting(
            filename=file.filename,
            predictions=[p.model_dump() for p in predictions_out],
            singapore_filtered=filtered,
            lat=lat,
            lng=lng,
        )
        sighting_id = record.get("id")
    except Exception as exc:
        logger.error("Supabase write failed: %s", exc)

    # 7. Return
    return PredictResponse(
        filename=file.filename,
        predictions=predictions_out,
        singapore_filtered=filtered,
        sighting_id=sighting_id,
        recording=recording,
    )