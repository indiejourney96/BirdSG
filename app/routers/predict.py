"""
predict.py — POST /predict endpoint.

Pipeline:
  1. Validate file type and size.
  2. Run EfficientNet-B0 inference → top-10 ImageNet predictions.
  3. Bird gate  — reject if the top prediction is not a bird class or
                  confidence is too low. Returns HTTP 422 with a clear message.
  4. Singapore filter — keep only predictions matching Singapore species.
  5. Return top-3 Singapore matches, or best unfiltered prediction as fallback.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.bird_labels import BIRD_CONFIDENCE_THRESHOLD, is_bird_image
from app.model import predict_top_k
from app.singapore_birds import is_singapore_bird

ALLOWED_TYPES    = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
TOP_K_MODEL      = 10   # fetch more candidates so the filter has room to work
TOP_K_RETURN     = 3    # max Singapore matches to return

router = APIRouter()


class PredictionItem(BaseModel):
    label: str
    confidence: float
    singapore_match: bool


class PredictResponse(BaseModel):
    filename: str
    predictions: list[PredictionItem]
    singapore_filtered: bool  # True = SG filter applied; False = fallback used


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):

    # ── 1. Validate ───────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed: {sorted(ALLOWED_TYPES)}",
        )

    image_bytes = await file.read()
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_SIZE_MB} MB.",
        )

    # ── 2. Inference ──────────────────────────────────────────────────────
    try:
        raw_results = predict_top_k(image_bytes, k=TOP_K_MODEL)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not process image: {exc}")

    # ── 3. Bird gate ──────────────────────────────────────────────────────
    # Evaluate the top prediction only — if the model's best guess isn't a
    # bird with enough confidence, the image is almost certainly not a bird.
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

    # ── 4. Singapore filter ───────────────────────────────────────────────
    sg_matches = [r for r in raw_results if is_singapore_bird(r.label)]

    if sg_matches:
        final    = sg_matches[:TOP_K_RETURN]
        filtered = True
    else:
        # Bird confirmed but no Singapore species match — return best guess
        # with singapore_filtered=False so the UI can show a softer warning.
        final    = raw_results[:1]
        filtered = False

    return PredictResponse(
        filename=file.filename,
        predictions=[
            PredictionItem(
                label=r.label,
                confidence=r.confidence,
                singapore_match=is_singapore_bird(r.label),
            )
            for r in final
        ],
        singapore_filtered=filtered,
    )