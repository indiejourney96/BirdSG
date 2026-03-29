"""
predict.py — POST /predict endpoint.

Pipeline:
    1. Validate file type and size
    2. Run EfficientNet-B0 inference (top 10)
    3. Bird gate — reject non-bird images
    4. Singapore filter — keep local species matches
    5. Persist to Supabase (failures are logged, never raised)
    6. Return response
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.bird_labels import BIRD_CONFIDENCE_THRESHOLD, is_bird_image
from app.database import save_sighting
from app.model import predict_top_k
from app.singapore_birds import is_singapore_bird

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


class PredictResponse(BaseModel):
    filename: str
    predictions: list[PredictionItem]
    singapore_filtered: bool
    sighting_id: str | None = None


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):

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
    if not is_bird_image(top.label, top.confidence):
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
    sg_matches = [r for r in raw_results if is_singapore_bird(r.label)]
    final    = sg_matches[:TOP_K_RETURN] if sg_matches else raw_results[:1]
    filtered = bool(sg_matches)

    predictions_out = [
        PredictionItem(
            label=r.label,
            confidence=r.confidence,
            singapore_match=is_singapore_bird(r.label),
        )
        for r in final
    ]

    # 5. Persist to Supabase
    sighting_id: str | None = None
    try:
        record = save_sighting(
            filename=file.filename,
            predictions=[p.model_dump() for p in predictions_out],
            singapore_filtered=filtered,
        )
        sighting_id = record.get("id")
    except Exception as exc:
        logger.error("Supabase write failed: %s", exc)

    # 6. Return
    return PredictResponse(
        filename=file.filename,
        predictions=predictions_out,
        singapore_filtered=filtered,
        sighting_id=sighting_id,
    )