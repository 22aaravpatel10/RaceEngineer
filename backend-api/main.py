"""
Overcut API - FastF1 Data Engine
Port: 8000
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import fastf1

from api.routes import router

# Initialize FastF1 Cache
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../f1_cache')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

# FastAPI App
app = FastAPI(
    title="Overcut F1 API",
    description="High-performance F1 Telemetry & Strategy API",
    version="2.0.0"
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6000", "http://127.0.0.1:6000", "http://localhost:4000", "http://127.0.0.1:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "online", "service": "Overcut F1 API", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
