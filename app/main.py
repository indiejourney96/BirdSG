"""
main.py — FastAPI application entry point.

The lifespan context manager warms the model at startup so the first
request doesn't pay the load penalty (~1-2s on CPU).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.model import load_model
from app.routers import predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm model on startup — runs once, cached via lru_cache in model.py
    load_model()
    yield
    # (no teardown needed — model lives for the process lifetime)


app = FastAPI(
    title="Bird ID API",
    description="EfficientNet-B0 image classification for bird identification",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten to your frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}