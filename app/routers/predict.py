import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10

router = APIRouter()


class Prediction(BaseModel):
    label: str
    confidence: float


class PredictResponse(BaseModel):
    predictions: list[Prediction]
    filename: str


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {ALLOWED_TYPES}",
        )

    # Save to tmp with a unique name to avoid collisions
    suffix = Path(file.filename).suffix or ".jpg"
    tmp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"

    try:
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Enforce size limit after save
        size_mb = tmp_path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_SIZE_MB} MB.",
            )

        # --- Replace this block with real model inference in Phase 2 ---
        predictions = _dummy_predict()
        # ----------------------------------------------------------------

    finally:
        # Always clean up the temp file
        if tmp_path.exists():
            tmp_path.unlink()

    return PredictResponse(predictions=predictions, filename=file.filename)


def _dummy_predict() -> list[Prediction]:
    """Placeholder — swap in real model inference here."""
    return [
        Prediction(label="Eurasian Tree Sparrow", confidence=0.82),
        Prediction(label="Oriental Magpie-Robin", confidence=0.61),
        Prediction(label="Common Myna", confidence=0.45),
    ]
