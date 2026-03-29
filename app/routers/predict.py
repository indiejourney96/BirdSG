"""
predict.py — POST /predict endpoint.

    ┌─────────────────────────────────────────────────────────┐
    │  1. VALIDATE      file type + size                      │
    │  2. INFER         EfficientNet-B0 → top 10 predictions  │
    │  3. BIRD GATE     reject non-bird images   (bird_gate)  │
    │  4. SG FILTER     keep Singapore species   (sg_filter)  │
    │  5. PERSIST       write to Supabase        (database)   │
    │  6. RESPOND       return top 3 results                  │
    └─────────────────────────────────────────────────────────┘

"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.bird_gate import BIRD_CONFIDENCE_THRESHOLD, passes_bird_gate
from app.database import save_sighting
from app.model import predict_top_k
from app.sg_filter import is_singapore_species

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