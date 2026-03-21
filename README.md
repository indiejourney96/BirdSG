# Bird ID API

FastAPI backend using a pretrained **EfficientNet-B0** model for bird image classification.
Returns the top 5 ImageNet predictions with confidence scores.

## Folder Structure

```
bird-api/
├── app/
│   ├── main.py           # App entry point, lifespan warm-up, CORS
│   ├── model.py          # Model loading, preprocessing, inference
│   └── routers/
│       └── predict.py    # POST /predict endpoint
├── requirements.txt
└── README.md
```

## Run Locally (Windows PowerShell)

**1. Create and activate a virtual environment**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
> If blocked by execution policy:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**2. Install dependencies**
```powershell
pip install -r requirements.txt
```
> First run downloads the EfficientNet-B0 weights (~21 MB) from PyTorch Hub.
> They are cached locally after that.

**3. Start the server**
```powershell
uvicorn app.main:app --reload --port 8000
```
> You'll see `Model loaded` logged on startup — the model is ready before the first request.

**4. Test the endpoint**
```powershell
curl.exe -X POST http://localhost:8000/predict -F "file=@C:\path\to\bird.jpg"
```
Or open **http://localhost:8000/docs** and use the Swagger UI.

## Endpoints

| Method | Path       | Description                        |
|--------|------------|------------------------------------|
| GET    | /health    | Health check                       |
| POST   | /predict   | Upload image → top 5 predictions   |

## Sample Response

```json
{
  "filename": "kingfisher.jpg",
  "predictions": [
    {"label": "kingfisher", "confidence": 0.8214},
    {"label": "bee eater",  "confidence": 0.0721},
    {"label": "jacamar",    "confidence": 0.0340},
    {"label": "hornbill",   "confidence": 0.0187},
    {"label": "toucan",     "confidence": 0.0104}
  ]
}
```

## Architecture Notes

| Concern | Where |
|---|---|
| Model load + caching | `app/model.py` → `load_model()` via `lru_cache` |
| Image preprocessing | `app/model.py` → `preprocess()` |
| Inference | `app/model.py` → `predict_top_k()` |
| HTTP handling | `app/routers/predict.py` |
| Startup warm-up | `app/main.py` → `lifespan()` |

## Performance (CPU)

- Model warm-up: ~2–4 s at startup (once only)
- Per-request inference: **~300–800 ms** on a modern CPU
- No GPU required

## Next Step — Singapore Bird Filtering (Phase 3)

In `predict.py`, filter `results` against the eBird Singapore species list
before returning, so only locally relevant birds surface:

```python
SG_BIRDS = {"kingfisher", "sunbird", ...}  # from eBird API
results = [r for r in results if any(sg in r.label.lower() for sg in SG_BIRDS)]
```