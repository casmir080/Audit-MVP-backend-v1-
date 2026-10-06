"""
Entry point. Run with: uvicorn main:app --reload
Then open http://localhost:8000/docs to try it end to end.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingest import router as ingest_router
from chat import router as chat_router
from pipeline import router as pipeline_router
from evidence_cbn import score_readiness

# --- Pydantic Models ---
class CBNEvidenceSubmission(BaseModel):
    evidence_ids: list[str]


# --- App Setup ---
app = FastAPI(title="Audit MVP", version="0.1.0")

# Comma-separated list, e.g. "http://localhost:3000,https://your-app.vercel.app"
# Set ALLOWED_ORIGINS in Render's environment variables once you have the
# real Vercel URL - no code change needed when the frontend URL changes.
_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(pipeline_router)


# --- Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/evidence/cbn/score")
async def score_cbn_localisation(payload: CBNEvidenceSubmission):
    return score_readiness(set(payload.evidence_ids))