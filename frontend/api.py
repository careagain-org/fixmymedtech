# api.py — HTTP client that calls the FastAPI backend

import httpx
import os

API_URL = os.getenv("API_URL", "http://localhost:8888")


async def _get(path: str, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_URL}{path}", headers=headers)
        r.raise_for_status()
        return r.json()


async def _post(path: str, data: dict, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{API_URL}{path}", json=data, headers=headers)
        r.raise_for_status()
        return r.json()


async def _patch(path: str, data: dict, token: str = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient() as client:
        r = await client.patch(f"{API_URL}{path}", json=data, headers=headers)
        r.raise_for_status()
        return r.json()


# ── Auth ─────────────────────────────────────────────────────
async def login(email: str, password: str):
    return await _post("/api/auth/login", {"email": email, "password": password})

async def signup(email: str, password: str, full_name: str, role: str, organization_id: str = None):
    data = {"email": email, "password": password, "full_name": full_name, "role": role}
    if organization_id:
        data["organization_id"] = organization_id
    return await _post("/api/auth/signup", data)

async def get_organizations():
    return await _get("/api/auth/organizations")


# ── Dashboard ────────────────────────────────────────────────
async def get_dashboard_stats(token: str):
    return await _get("/api/dashboard/stats", token)


# ── Devices ──────────────────────────────────────────────────
async def get_devices(token: str, status: str = None):
    path = f"/api/devices/?status={status}" if status else "/api/devices/"
    return await _get(path, token)

async def get_device(token: str, device_id: str):
    return await _get(f"/api/devices/{device_id}", token)

async def get_device_public(device_id: str):
    return await _get(f"/api/devices/public/{device_id}")

async def get_categories(token: str):
    return await _get("/api/devices/categories", token)

async def create_device(token: str, data: dict):
    return await _post("/api/devices", data, token)

async def update_device(token: str, device_id: str, data: dict):
    return await _patch(f"/api/devices/{device_id}", data, token)


# ── Faults ───────────────────────────────────────────────────
async def submit_fault_public(data: dict):
    return await _post("/api/faults/public", data)