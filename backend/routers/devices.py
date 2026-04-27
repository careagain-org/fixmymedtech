# routers/devices.py

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from routers.deps import get_supabase, get_current_user

router = APIRouter()


class DeviceCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    category_id: Optional[str] = None
    manufacture_year: Optional[int] = None
    acquisition_date: Optional[date] = None
    acquisition_type: Optional[str] = "purchased"
    location: Optional[str] = None
    notes: Optional[str] = None
    next_maintenance: Optional[date] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    next_maintenance: Optional[date] = None


# ── Public endpoint: scanned via QR (no auth needed) ──────────
@router.get("/public/{device_id}")
async def get_device_public(device_id: str, request: Request):
    """
    Called when someone scans the QR code on a device.
    Returns device info + documents + recent fault reports.
    No authentication required.
    """
    sb = get_supabase(request)

    device = sb.table("devices").select(
        "*, device_categories(name, icon), organizations(name, country)"
    ).eq("id", device_id).single().execute()

    if not device.data:
        raise HTTPException(status_code=404, detail="Device not found")

    docs = sb.table("documents").select("*").eq("device_id", device_id).execute()

    recent_faults = sb.table("fault_reports").select(
        "id, reported_at, description, severity, status"
    ).eq("device_id", device_id).order("reported_at", desc=True).limit(5).execute()

    return {
        "device": device.data,
        "documents": docs.data,
        "recent_faults": recent_faults.data,
    }


# ── Protected endpoints (require auth) ───────────────────────
@router.get("/")
async def list_devices(
    request: Request,
    status: Optional[str] = None,
    user=Depends(get_current_user),
):
    sb = get_supabase(request)

    # Get user's organization
    profile = sb.table("profiles").select("organization_id").eq("id", user.id).single().execute()
    org_id = profile.data["organization_id"]

    query = sb.table("devices").select(
        "*, device_categories(name, icon)"
    ).eq("organization_id", org_id).order("name")

    if status:
        query = query.eq("status", status)

    result = query.execute()
    return result.data


@router.get("/{device_id}")
async def get_device(device_id: str, request: Request, user=Depends(get_current_user)):
    sb = get_supabase(request)

    device = sb.table("devices").select(
        "*, device_categories(name, icon), organizations(name)"
    ).eq("id", device_id).single().execute()

    if not device.data:
        raise HTTPException(status_code=404, detail="Device not found")

    logs = sb.table("maintenance_logs").select(
        "*, profiles(full_name)"
    ).eq("device_id", device_id).order("performed_at", desc=True).limit(10).execute()

    faults = sb.table("fault_reports").select("*").eq(
        "device_id", device_id
    ).order("reported_at", desc=True).limit(10).execute()

    docs = sb.table("documents").select("*").eq("device_id", device_id).execute()

    return {
        "device": device.data,
        "maintenance_logs": logs.data,
        "fault_reports": faults.data,
        "documents": docs.data,
    }


@router.post("/")
async def create_device(body: DeviceCreate, request: Request, user=Depends(get_current_user)):
    sb = get_supabase(request)

    profile = sb.table("profiles").select("organization_id, role").eq("id", user.id).single().execute()
    if profile.data["role"] not in ("admin", "technician"):
        raise HTTPException(status_code=403, detail="Not authorized")

    payload = body.model_dump(exclude_none=True)
    payload["organization_id"] = profile.data["organization_id"]
    if "acquisition_date" in payload:
        payload["acquisition_date"] = str(payload["acquisition_date"])
    if "next_maintenance" in payload:
        payload["next_maintenance"] = str(payload["next_maintenance"])

    result = sb.table("devices").insert(payload).execute()
    return result.data[0]


@router.patch("/{device_id}")
async def update_device(device_id: str, body: DeviceUpdate, request: Request, user=Depends(get_current_user)):
    sb = get_supabase(request)

    profile = sb.table("profiles").select("role").eq("id", user.id).single().execute()
    if profile.data["role"] not in ("admin", "technician"):
        raise HTTPException(status_code=403, detail="Not authorized")

    payload = body.model_dump(exclude_none=True)
    if "next_maintenance" in payload:
        payload["next_maintenance"] = str(payload["next_maintenance"])

    result = sb.table("devices").update(payload).eq("id", device_id).execute()
    return result.data[0]


@router.delete("/{device_id}")
async def delete_device(device_id: str, request: Request, user=Depends(get_current_user)):
    sb = get_supabase(request)

    profile = sb.table("profiles").select("role").eq("id", user.id).single().execute()
    if profile.data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete devices")

    sb.table("devices").delete().eq("id", device_id).execute()
    return {"message": "Device deleted"}