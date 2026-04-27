# ============================================================
# MedTrack QR — FastAPI Backend
# ============================================================
# Install: pip install fastapi uvicorn supabase python-dotenv pydantic
# Run:     uvicorn main:app --reload
# ============================================================

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from starlette.responses import RedirectResponse

from routers import devices, fault_reports, dashboard, auth
from config.supabase_config import supa_client

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.supabase = supa_client
    yield

app = FastAPI(
    title="MedTrack QR API",
    description="Medical equipment management for LMICs",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False, 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api/auth",    tags=["auth"])
app.include_router(devices.router,      prefix="/api/devices", tags=["devices"])
app.include_router(fault_reports.router,prefix="/api/faults",  tags=["faults"])
app.include_router(dashboard.router,    prefix="/api/dashboard",tags=["dashboard"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "medtrack-api"}

@app.get('/')
def default_route():
    return RedirectResponse(url="/docs")