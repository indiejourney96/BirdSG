# Bird ID API

Minimal FastAPI backend for bird image classification.

## Folder Structure

```
bird-api/
├── app/
│   ├── main.py           # App entry point, CORS, router registration
│   └── routers/
│       └── predict.py    # POST /predict endpoint
├── tmp/                  # Temp image storage (auto-cleaned per request)
├── requirements.txt
└── README.md
```

## Run Locally

**1. Create and activate a virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Start the server**
```bash
uvicorn app.main:app --reload --port 8000
```

**4. Test the endpoint**
```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@/path/to/bird.jpg"
```

Or open the interactive docs at: http://localhost:8000/docs

## Endpoints

| Method | Path       | Description              |
|--------|------------|--------------------------|
| GET    | /health    | Health check             |
| POST   | /predict   | Upload image, get predictions |

## Sample Response

```json
{
  "predictions": [
    {"label": "Eurasian Tree Sparrow", "confidence": 0.82},
    {"label": "Oriental Magpie-Robin", "confidence": 0.61},
    {"label": "Common Myna",           "confidence": 0.45}
  ],
  "filename": "bird.jpg"
}
```

## Swapping in a Real Model

In `app/routers/predict.py`, replace `_dummy_predict()` with your actual
inference logic. The `tmp_path` variable holds the saved image path and is
available inside the `try` block before cleanup.

## Deploy to Render / Railway

Set the start command to:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
