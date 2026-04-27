# routers/fault_reports.py

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from routers.deps import get_supabase, get_current_user

router = APIRouter()


class FaultReportCreate(BaseModel):
    device_id: str
    description: str
    severity: str = "medium"
    reporter_name: Optional[str] = None  # for anonymous reports


class FaultStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


# ── Public: submit a fault report (no auth — via QR page) ────
@router.post("/public")
async def submit_fault_public(body: FaultReportCreate, request: Request):
    """Anyone who scans the QR can report a fault. No account needed."""
    sb = get_supabase(request)

    # Verify device exists
    device = sb.table("devices").select("id, name").eq("id", body.device_id).single().execute()
    if not device.data:
        raise HTTPException(status_code=404, detail="Device not found")

    result = sb.table("fault_reports").insert({
        "device_id": body.device_id,
        "description": body.description,
        "severity": body.severity,
        "reporter_name": body.reporter_name or "Anonymous",
        "status": "open",
    }).execute()

    # Update device status if critical
    if body.severity in ("high", "critical"):
        sb.table("devices").update({"status": "fault"}).eq("id", body.device_id).execute()

    return {"message": "Fault report submitted. A technician will be notified.", "id": result.data[0]["id"]}


# ── Protected: list all faults for the organization ──────────
@router.get("/")
async def list_faults(
    request: Request,
    status: Optional[str] = None,
    user=Depends(get_current_user),
):
    sb = get_supabase(request)

    profile = sb.table("profiles").select("organization_id").eq("id", user.id).single().execute()
    org_id = profile.data["organization_id"]

    # Get device IDs for this org
    devices = sb.table("devices").select("id").eq("organization_id", org_id).execute()
    device_ids = [d["id"] for d in devices.data]

    query = sb.table("fault_reports").select(
        "*, devices(name, location)"
    ).in_("device_id", device_ids).order("reported_at", desc=True)

    if status:
        query = query.eq("status", status)

    result = query.execute()
    return result.data


# ── Protected: update fault status ───────────────────────────
@router.patch("/{fault_id}")
async def update_fault(fault_id: str, body: FaultStatusUpdate, request: Request, user=Depends(get_current_user)):
    sb = get_supabase(request)

    profile = sb.table("profiles").select("role").eq("id", user.id).single().execute()
    if profile.data["role"] not in ("admin", "technician"):
        raise HTTPException(status_code=403, detail="Not authorized")

    payload = {"status": body.status}
    if body.resolution_notes:
        payload["resolution_notes"] = body.resolution_notes
    if body.status == "resolved":
        from datetime import datetime, timezone
        payload["resolved_at"] = datetime.now(timezone.utc).isoformat()

    result = sb.table("fault_reports").update(payload).eq("id", fault_id).execute()
    return result.data[0]