from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import fastf1

# Initialize FastF1 Cache
fastf1.Cache.enable_cache('./cache')

app = FastAPI(title="Overcut F1 API")

# 1. CORS Middleware (Allow Frontend to talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. NO-CACHE Middleware (Crucial Fix for Data Sync)
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    # Force browser to always fetch new data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Include Routes
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Using port 8000 to match existing project configuration
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
