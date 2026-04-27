# routers/dashboard.py

from fastapi import APIRouter, Request, Depends
from routers.deps import get_supabase, get_current_user

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(request: Request, user=Depends(get_current_user)):
    """
    Returns aggregated stats for the admin dashboard:
    device counts by status, open faults, upcoming maintenance.
    """
    sb = get_supabase(request)

    profile = sb.table("profiles").select("organization_id").eq("id", user.id).single().execute()
    org_id = profile.data["organization_id"]

    # All devices for this org
    devices = sb.table("devices").select("id, status, next_maintenance").eq("organization_id", org_id).execute()
    all_devices = devices.data

    total = len(all_devices)
    by_status = {"operational": 0, "maintenance": 0, "fault": 0, "decommissioned": 0}
    for d in all_devices:
        s = d.get("status", "operational")
        by_status[s] = by_status.get(s, 0) + 1

    # Devices with maintenance overdue or due in next 30 days
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=30)

    overdue = []
    due_soon = []
    for d in all_devices:
        nm = d.get("next_maintenance")
        if nm:
            try:
                nm_dt = datetime.fromisoformat(nm.replace("Z", "+00:00")) if "T" in nm else datetime.fromisoformat(nm + "T00:00:00+00:00")
                if nm_dt < now:
                    overdue.append(d["id"])
                elif nm_dt <= soon:
                    due_soon.append(d["id"])
            except Exception:
                pass

    # Open fault reports
    device_ids = [d["id"] for d in all_devices]
    open_faults = sb.table("fault_reports").select(
        "id, severity, reported_at, devices(name, location)"
    ).in_("device_id", device_ids).eq("status", "open").order("reported_at", desc=True).limit(10).execute()

    # Recent maintenance
    recent_maintenance = sb.table("maintenance_logs").select(
        "id, performed_at, type, devices(name)"
    ).in_("device_id", device_ids).order("performed_at", desc=True).limit(5).execute()

    return {
        "total_devices": total,
        "by_status": by_status,
        "maintenance_overdue": len(overdue),
        "maintenance_due_soon": len(due_soon),
        "open_faults": open_faults.data,
        "recent_maintenance": recent_maintenance.data,
    }