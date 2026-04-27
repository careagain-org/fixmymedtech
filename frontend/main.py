# main.py — FixMyMedTech FastHTML frontend

from fasthtml.common import *
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
import os, httpx
from dotenv import load_dotenv

load_dotenv()

import api as backend
from components import *

SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")

app, rt = fast_app(secret_key=SECRET,static="/static/")
app.add_middleware(SessionMiddleware, secret_key=SECRET)


# ── Auth helpers ─────────────────────────────────────────────

def get_token(req):
    return req.session.get("token")

def clear_session(req):
    """Clear all session data — call when token is invalid/expired."""
    req.session.clear()

async def verify_token(req) -> bool:
    """
    Verify the token is still valid by calling a lightweight API endpoint.
    Returns True if valid, False if expired or invalid.
    """
    token = get_token(req)
    if not token:
        return False
    try:
        await backend.get_dashboard_stats(token)
        return True
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            clear_session(req)
            return False
        return True  # other errors (500 etc) don't mean token is invalid
    except Exception:
        return True  # network errors don't mean token is invalid

def require_auth(req):
    """
    Fast check — just verifies session has a token.
    For full token validation use require_auth_verified.
    """
    token = get_token(req)
    if not token:
        return None, RedirectResponse("/login", status_code=302)
    return token, None

async def require_auth_verified(req):
    """
    Full check — verifies token is still valid with the API.
    Use on sensitive routes like dashboard.
    """
    token = get_token(req)
    if not token:
        return None, RedirectResponse("/login", status_code=302)
    try:
        # Validate by hitting a protected endpoint
        await backend._get("/api/dashboard/stats", token)
        return token, None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            clear_session(req)
            return None, RedirectResponse("/login?expired=1", status_code=302)
        return token, None
    except Exception:
        return token, None


# ══════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════

@rt("/login")
async def get(req, expired: str = ""):
    # Only redirect if token is actually still valid
    token = get_token(req)
    if token:
        try:
            await backend._get("/api/dashboard/stats", token)
            return RedirectResponse("/dashboard", status_code=302)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                clear_session(req)  # clear expired token, show login
        except Exception:
            return RedirectResponse("/dashboard", status_code=302)

    expired_msg = Div("Your session has expired. Please sign in again.",
                      cls="alert alert-warning") if expired else ""
    form = Form(
        Div(
            Div(
                Div(
                    Span("✚", cls="brand-icon"),
                    H1("FixMyMedTech"),
                    P("Medical equipment management for LMICs"),
                    cls="auth-brand"
                ),
                expired_msg,
                Div(
                    Label("Email", cls="label", for_="email"),
                    Input(id="email", name="email", type="email",
                          placeholder="you@hospital.org", cls="input"),
                    cls="form-group"
                ),
                Div(
                    Label("Password", cls="label", for_="password"),
                    Input(id="password", name="password", type="password",
                          placeholder="••••••••", cls="input"),
                    cls="form-group"
                ),
                Button("Sign in", type="submit", cls="btn btn-primary",
                       style="width:100%;justify-content:center;margin-top:4px;"),
                P(
                    "New to MedTrack? ", A("Create an account", href="/signup"),
                    cls="auth-link", style="margin-top:12px;"
                ),
                cls="auth-card"
            ),
            Div(
                Blockquote(
                    '"40–70% of medical equipment in LMICs is out of service. ',
                    Em("MedTrack helps change that."),
                    '"',
                    cls="auth-quote"
                ),
                cls="auth-bg"
            ),
            cls="auth-wrap"
        ),
        method="post", action="/login"
    )

    return pub_shell(form, title="Login — FixMyMedTech")


@rt("/login")
async def post(req, email: str, password: str):
    try:
        res = await backend.login(email, password)
        req.session["token"] = res["access_token"]
        req.session["user_email"] = res["user"]["email"]
        return RedirectResponse("/dashboard", status_code=302)
    except httpx.HTTPStatusError:
        form_error = Div(
            Div(
                Div(
                    Span("✚", cls="brand-icon"),
                    H1("FixMyMedTech"),
                    P("Medical equipment management for LMICs"),
                    cls="auth-brand"
                ),
                Div("Invalid email or password.", cls="alert alert-error"),
                Div(
                    Label("Email", cls="label", for_="email"),
                    Input(id="email", name="email", type="email",
                          value=email, cls="input"),
                    cls="form-group"
                ),
                Div(
                    Label("Password", cls="label", for_="password"),
                    Input(id="password", name="password", type="password",
                          cls="input"),
                    cls="form-group"
                ),
                Button("Sign in", type="submit", cls="btn btn-primary",
                       style="width:100%;justify-content:center;margin-top:4px;"),
                P("New to MedTrack? ", A("Create an account", href="/signup"),
                  cls="auth-link", style="margin-top:12px;"),
                cls="auth-card"
            ),
            Div(
                Blockquote('"40–70% of medical equipment in LMICs is out of service. ',
                           Em("MedTrack helps change that."), '"', cls="auth-quote"),
                cls="auth-bg"
            ),
            cls="auth-wrap"
        )
        return pub_shell(Form(form_error, method="post", action="/login"),
                         title="Login — FixMyMedTech")


@rt("/logout")
async def get(req):
    req.session.clear()
    return RedirectResponse("/login", status_code=302)


@rt("/signup")
async def get(req):
    if get_token(req):
        return RedirectResponse("/dashboard", status_code=302)

    try:
        orgs = await backend.get_organizations()
    except Exception:
        orgs = []

    org_options = [Option("— Select your organisation —", value="")]
    org_options += [Option(f"{o['name']} ({o['country']})", value=o["id"]) for o in orgs]

    content = Div(
        Div(
            Div(
                Span(
                    Img(src=os.getenv("LOGO_URL"),
                    style="height:56px; width:auto; display:block; margin-bottom:10px;"),
                    cls="brand-icon"),
                H1("Create account"),
                P("Join FixMyMedTech to manage your hospital's equipment"),
                cls="auth-brand"
            ),
            Div(
                Label("Full name", cls="label", for_="full_name"),
                Input(id="full_name", name="full_name", type="text",
                      placeholder="Dr. Jane Smith", cls="input"),
                cls="form-group"
            ),
            Div(
                Label("Email", cls="label", for_="email"),
                Input(id="email", name="email", type="email",
                      placeholder="you@hospital.org", cls="input"),
                cls="form-group"
            ),
            Div(
                Div(
                    Label("Password", cls="label", for_="password"),
                    Input(id="password", name="password", type="password",
                          placeholder="Min. 8 characters", cls="input"),
                    cls="form-group"
                ),
                Div(
                    Label("Confirm password", cls="label", for_="password2"),
                    Input(id="password2", name="password2", type="password",
                          placeholder="Repeat password", cls="input"),
                    cls="form-group"
                ),
                cls="form-row"
            ),
            Div(
                Label("Organisation", cls="label", for_="org"),
                Select(*org_options, id="org", name="organization_id", cls="input"),
                cls="form-group"
            ),
            Div(
                Label("Role", cls="label"),
                Div(
                    Label(Input(type="radio", name="role", value="clinical_staff", checked=True),
                          " Clinical staff (nurse, doctor)"),
                    Label(Input(type="radio", name="role", value="technician"),
                          " Biomedical technician"),
                    Label(Input(type="radio", name="role", value="admin"),
                          " Hospital administrator"),
                    style="display:flex;flex-direction:column;gap:6px;font-size:0.875rem;"
                ),
                cls="form-group"
            ),
            Button("Create account", type="submit", cls="btn btn-primary",
                   style="width:100%;justify-content:center;margin-top:8px;"),
            P("Already have an account? ", A("Sign in", href="/login"),
              cls="auth-link", style="margin-top:12px;"),
            cls="auth-card"
        ),
        Div(
            Div(
                Div(
                    Span("1", cls="step-num"), 
                    Div(P("Create your account", style="color:#fff;font-weight:500;margin:0;"),
                        P("Register with your hospital email",
                          style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin:0;")),
                    style="display:flex;gap:14px;align-items:flex-start;margin-bottom:24px;"
                ),
                Div(
                    Span("2", cls="step-num"),
                    Div(P("Confirm your email", style="color:#fff;font-weight:500;margin:0;"),
                        P("Click the link we send you",
                          style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin:0;")),
                    style="display:flex;gap:14px;align-items:flex-start;margin-bottom:24px;"
                ),
                Div(
                    Span("3", cls="step-num"),
                    Div(P("Start tracking", style="color:#fff;font-weight:500;margin:0;"),
                        P("Manage your equipment fleet",
                          style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin:0;")),
                    style="display:flex;gap:14px;align-items:flex-start;"
                ),
            ),
            cls="auth-bg"
        ),
        cls="auth-wrap"
    )

    return pub_shell(
        Form(content, method="post", action="/signup"),
        title="Sign up — FixMyMedTech"
    )


@rt("/signup")
async def post(req, full_name: str, email: str, password: str,
               password2: str, role: str, organization_id: str = ""):
    errors = []
    if not full_name:     errors.append("Full name is required.")
    if not email:         errors.append("Email is required.")
    if len(password) < 8: errors.append("Password must be at least 8 characters.")
    if password != password2: errors.append("Passwords do not match.")

    if not errors:
        try:
            await backend.signup(
                email=email, password=password, full_name=full_name,
                role=role, organization_id=organization_id or None
            )
            success = pub_shell(
                Div(
                    Div(
                        Div("✓", style="width:56px;height:56px;background:var(--c-green-lt);color:var(--c-green);border-radius:50%;font-size:1.4rem;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;"),
                        H2("Check your email"),
                        P(f"We sent a confirmation link to ", Strong(email),
                          ". Click it to activate your account."),
                        A("Go to login", href="/login", cls="btn btn-primary",
                          style="margin-top:20px;"),
                        style="text-align:center;padding:60px 40px;"
                    ),
                    style="max-width:440px;margin:80px auto;"
                )
            )
            return success
        except Exception as e:
            errors.append(str(e))

    error_html = Div(*[Div(e, cls="alert alert-error") for e in errors])
    return RedirectResponse(f"/signup?error={'|'.join(errors)}", status_code=302)


# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════

@rt("/dashboard")
async def get(req):
    token, redirect = require_auth(req)
    if redirect: return redirect

    try:
        stats = await backend.get_dashboard_stats(token)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            clear_session(req)
            return RedirectResponse("/login?expired=1", status_code=302)
        stats = {}
    except Exception:
        stats = {}

    by_status = stats.get("by_status", {})
    total = stats.get("total_devices", 0)
    pct = round((by_status.get("operational", 0) / total) * 100) if total else 0

    stat_cards = Div(
        Div(
            Div("Total devices", cls="stat-label"),
            Div(str(total), cls="stat-num"),
            Div(style=f"height:3px;background:var(--c-bg-2);border-radius:2px;margin:8px 0 3px;overflow:hidden;",
                children=[Div(style=f"width:{pct}%;height:100%;background:var(--c-green);border-radius:2px;")]),
            Div(f"{pct}% operational", cls="stat-sub"),
            cls="stat-card"
        ),
        Div(Div("Operational", cls="stat-label"),
            Div(str(by_status.get("operational", 0)), cls="stat-num"), cls="stat-card g"),
        Div(Div("Maintenance", cls="stat-label"),
            Div(str(by_status.get("maintenance", 0)), cls="stat-num"), cls="stat-card a"),
        Div(Div("Fault / down", cls="stat-label"),
            Div(str(by_status.get("fault", 0)), cls="stat-num"), cls="stat-card r"),
        Div(Div("Maint. overdue", cls="stat-label"),
            Div(str(stats.get("maintenance_overdue", 0)), cls="stat-num"),
            Div("Needs attention", cls="stat-sub"), cls="stat-card a"),
        Div(Div("Due in 30 days", cls="stat-label"),
            Div(str(stats.get("maintenance_due_soon", 0)), cls="stat-num"),
            Div("Scheduled soon", cls="stat-sub"), cls="stat-card"),
        cls="stat-grid"
    )

    # Open faults
    fault_rows = []
    for f in stats.get("open_faults", []):
        device = f.get("devices") or {}
        fault_rows.append(
            Div(
                Div(
                    Div(device.get("name", "Unknown"), style="font-size:0.875rem;font-weight:500;color:var(--c-text);"),
                    Div(device.get("location", ""), style="font-size:0.75rem;color:var(--c-text-3);"),
                    Div(f.get("description", "")[:80], style="font-size:0.8rem;color:var(--c-text-3);margin-top:2px;"),
                ),
                Div(status_badge(f.get("severity", "medium"), "severity"),
                    Div(fmt_date(f.get("reported_at", "")),
                        style="font-size:0.72rem;color:var(--c-text-3);margin-top:3px;"),
                    style="text-align:right;flex-shrink:0;"),
                style="display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid var(--c-border);"
            )
        )

    # Recent maintenance
    maint_rows = []
    for m in stats.get("recent_maintenance", []):
        device = m.get("devices") or {}
        color = "var(--c-green)" if m.get("type") == "preventive" else "var(--c-amber)"
        maint_rows.append(
            Div(
                Div(style=f"width:7px;height:7px;border-radius:50%;background:{color};flex-shrink:0;"),
                Div(
                    Div(device.get("name", "—"), style="font-size:0.875rem;font-weight:500;color:var(--c-text);"),
                    Div(f"{m.get('type', '')} · {fmt_date(m.get('performed_at', ''))}",
                        style="font-size:0.75rem;color:var(--c-text-3);"),
                ),
                style="display:flex;align-items:center;gap:10px;"
            )
        )

    two_col = Div(
        Div(
            H3("Open fault reports", style="margin-bottom:12px;"),
            *fault_rows if fault_rows else [P("No open faults.", style="color:var(--c-text-3);padding:16px 0;")],
            cls="card"
        ),
        Div(
            H3("Recent maintenance", style="margin-bottom:12px;"),
            *maint_rows if maint_rows else [P("No maintenance logged yet.", style="color:var(--c-text-3);padding:16px 0;")],
            cls="card"
        ),
        cls="two-col"
    )

    content = Div(
        Div(
            Div(H1("Dashboard"), P("Overview of your equipment fleet", style="color:var(--c-text-3);")),
            A("+ Add device", href="/devices/new", cls="btn btn-primary"),
            cls="page-header"
        ),
        stat_cards,
        two_col,
    )

    return page_shell(content, current="/dashboard", title="Dashboard — FixMyMedTech")


# ══════════════════════════════════════════════════════════════
# DEVICES LIST
# ══════════════════════════════════════════════════════════════

@rt("/devices")
async def get(req, status: str = ""):
    token, redirect = require_auth(req)
    if redirect: return redirect

    try:
        devices = await backend.get_devices(token, status or None)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            clear_session(req)
            return RedirectResponse("/login?expired=1", status_code=302)
        devices = []
    except Exception:
        devices = []

    status_filters = [
        ("", "All"), ("operational", "Operational"),
        ("maintenance", "Maintenance"), ("fault", "Fault"),
        ("decommissioned", "Decommissioned"),
    ]

    pills = [
        A(label, href=f"/devices?status={val}",
          cls=f"pill {'active' if status == val else ''}")
        for val, label in status_filters
    ]

    rows = []
    for d in devices:
        cat = d.get("device_categories") or {}
        nm = d.get("next_maintenance", "")
        overdue = nm and nm < __import__("datetime").datetime.now().isoformat()
        rows.append(Tr(
            Td(Div(d.get("name", ""), style="font-weight:500;font-size:0.875rem;color:var(--c-text);"),
               Div(f"{d.get('manufacturer','')} {d.get('model','')}".strip(),
                   style="font-size:0.75rem;color:var(--c-text-3);")),
            Td(f"{cat.get('icon','🏥')} {cat.get('name','—')}", style="font-size:0.875rem;"),
            Td(d.get("location", "—"), style="font-size:0.875rem;"),
            Td(status_badge(d.get("status", "operational"))),
            Td(
                Span(fmt_date(nm), cls="overdue" if overdue else ""),
                Span("overdue", cls="overdue-tag") if overdue else ""
            ),
            Td(A("View", href=f"/devices/{d['id']}", cls="btn btn-secondary btn-sm")),
        ))

    table = Div(
        Table(
            Thead(Tr(Th("Device"), Th("Category"), Th("Location"),
                     Th("Status"), Th("Next maint."), Th(""))),
            Tbody(*rows) if rows else Tbody(
                Tr(Td("No devices found.", colspan="6",
                       style="text-align:center;padding:32px;color:var(--c-text-3);"))
            )
        ),
        cls="table-wrap"
    )

    content = Div(
        Div(
            Div(H1("Devices"), P(f"{len(devices)} device{'s' if len(devices)!=1 else ''} registered",
                                  style="color:var(--c-text-3);")),
            A("+ Add device", href="/devices/new", cls="btn btn-primary"),
            cls="page-header"
        ),
        Div(*pills, cls="toolbar"),
        table,
    )

    return page_shell(content, current="/devices", title="Devices — FixMyMedTech")


# ══════════════════════════════════════════════════════════════
# NEW DEVICE
# ══════════════════════════════════════════════════════════════

@rt("/devices/new")
async def get(req):
    token, redirect = require_auth(req)
    if redirect: return redirect

    try:
        categories = await backend.get_categories(token)
    except Exception:
        categories = []

    cat_options = [Option("— Select category —", value="")]
    cat_options += [Option(f"{c.get('icon','')} {c['name']}", value=c["id"]) for c in categories]

    form = Form(
        A("← Devices", href="/devices",
          style="font-size:0.875rem;color:var(--c-text-3);text-decoration:none;margin-bottom:20px;display:inline-block;"),
        H1("Add new device", style="margin-bottom:4px;"),
        P("Register a medical device to start tracking it", style="margin-bottom:20px;"),
        Div(
            H3("Basic information", style="font-size:1rem;margin-bottom:14px;color:var(--c-text-2);"),
            Div(
                Div(Label("Device name *", cls="label", for_="name"),
                    Input(id="name", name="name", cls="input", placeholder="e.g. Ventilator LTV 1200"),
                    cls="form-group"),
                Div(Label("Category", cls="label", for_="category"),
                    Select(*cat_options, id="category", name="category_id", cls="input"),
                    cls="form-group"),
                cls="form-row"
            ),
            Div(
                Div(Label("Manufacturer", cls="label"),
                    Input(name="manufacturer", cls="input", placeholder="e.g. GE Healthcare"),
                    cls="form-group"),
                Div(Label("Model", cls="label"),
                    Input(name="model", cls="input", placeholder="e.g. ProCare B40"),
                    cls="form-group"),
                cls="form-row"
            ),
            Div(
                Div(Label("Serial number", cls="label"),
                    Input(name="serial_number", cls="input", placeholder="SN-XXXXXX"),
                    cls="form-group"),
                Div(Label("Manufacture year", cls="label"),
                    Input(name="manufacture_year", type="number", cls="input",
                          placeholder="2018", min="1990", max="2030"),
                    cls="form-group"),
                cls="form-row"
            ),
            cls="card", style="margin-bottom:14px;"
        ),
        Div(
            H3("Location & acquisition", style="font-size:1rem;margin-bottom:14px;color:var(--c-text-2);"),
            Div(
                Div(Label("Location", cls="label"),
                    Input(name="location", cls="input", placeholder="e.g. ICU / Bed 4"),
                    cls="form-group"),
                Div(Label("Acquisition type", cls="label"),
                    Select(Option("Purchased", value="purchased"),
                           Option("Donated", value="donated"),
                           Option("Leased", value="leased"),
                           name="acquisition_type", cls="input"),
                    cls="form-group"),
                cls="form-row"
            ),
            Div(
                Div(Label("Acquisition date", cls="label"),
                    Input(name="acquisition_date", type="date", cls="input"),
                    cls="form-group"),
                Div(Label("Next maintenance due", cls="label"),
                    Input(name="next_maintenance", type="date", cls="input"),
                    cls="form-group"),
                cls="form-row"
            ),
            cls="card", style="margin-bottom:14px;"
        ),
        Div(
            H3("Notes", style="font-size:1rem;margin-bottom:14px;color:var(--c-text-2);"),
            Div(Textarea(name="notes", cls="input", placeholder="Any relevant notes…", rows="3"),
                cls="form-group"),
            cls="card", style="margin-bottom:14px;"
        ),
        Div(
            A("Cancel", href="/devices", cls="btn btn-secondary"),
            Button("Register device", type="submit", cls="btn btn-primary"),
            style="display:flex;justify-content:flex-end;gap:10px;"
        ),
        method="post", action="/devices/new",
        style="max-width:720px;"
    )

    return page_shell(form, current="/devices", title="Add device — FixMyMedTech")


@rt("/devices/new")
async def post(req, name: str, manufacturer: str = "", model: str = "",
               serial_number: str = "", category_id: str = "", location: str = "",
               acquisition_type: str = "purchased", acquisition_date: str = "",
               manufacture_year: str = "", next_maintenance: str = "", notes: str = ""):
    token, redirect = require_auth(req)
    if redirect: return redirect

    payload = {"name": name}
    if manufacturer:      payload["manufacturer"]     = manufacturer
    if model:             payload["model"]            = model
    if serial_number:     payload["serial_number"]    = serial_number
    if category_id:       payload["category_id"]      = category_id
    if location:          payload["location"]         = location
    if acquisition_type:  payload["acquisition_type"] = acquisition_type
    if acquisition_date:  payload["acquisition_date"] = acquisition_date
    if manufacture_year:  payload["manufacture_year"] = int(manufacture_year)
    if next_maintenance:  payload["next_maintenance"] = next_maintenance
    if notes:             payload["notes"]            = notes

    try:
        device = await backend.create_device(token, payload)
        return RedirectResponse(f"/devices/{device['id']}", status_code=302)
    except Exception as e:
        return RedirectResponse("/devices/new", status_code=302)


# ══════════════════════════════════════════════════════════════
# DEVICE DETAIL
# ══════════════════════════════════════════════════════════════

@rt("/devices/{device_id}")
async def get(req, device_id: str):
    token, redirect = require_auth(req)
    if redirect: return redirect

    try:
        data = await backend.get_device(token, device_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            clear_session(req)
            return RedirectResponse("/login?expired=1", status_code=302)
        return RedirectResponse("/devices", status_code=302)
    except Exception:
        return RedirectResponse("/devices", status_code=302)

    d = data.get("device", {})
    cat = d.get("device_categories") or {}
    org = d.get("organizations") or {}
    logs = data.get("maintenance_logs", [])
    faults = data.get("fault_reports", [])
    docs = data.get("documents", [])

    qr_url = f"{req.base_url}d/{device_id}"

    # Maintenance log rows
    log_rows = [
        Tr(
            Td(fmt_date(l.get("performed_at", "")), style="font-size:0.875rem;"),
            Td(Span(l.get("type",""), cls="badge badge-blue")),
            Td(l.get("description","—"), style="font-size:0.875rem;"),
            Td((l.get("profiles") or {}).get("full_name","—"), style="font-size:0.875rem;"),
            Td(f"${l['cost_usd']}" if l.get("cost_usd") else "—", style="font-size:0.875rem;"),
        ) for l in logs
    ]

    # Fault rows
    fault_rows = [
        Tr(
            Td(fmt_date(f.get("reported_at","")), style="font-size:0.875rem;"),
            Td(f.get("reporter_name","—"), style="font-size:0.875rem;"),
            Td(f.get("description",""), style="font-size:0.875rem;"),
            Td(status_badge(f.get("severity","medium"), "severity")),
            Td(status_badge(f.get("status","open"), "fault")),
        ) for f in faults
    ]

    content = Div(
        A("← Devices", href="/devices",
          style="font-size:0.875rem;color:var(--c-text-3);text-decoration:none;margin-bottom:14px;display:inline-block;"),
        Div(
            Div(
                Div(f"{cat.get('icon','🏥')} {cat.get('name','Device')}",
                    style="font-size:0.8rem;color:var(--c-text-3);margin-bottom:4px;"),
                H1(d.get("name",""), style="margin-bottom:4px;"),
                P(f"{d.get('manufacturer','')} {d.get('model','')} · {d.get('location','No location')}",
                  style="color:var(--c-text-3);"),
            ),
            Div(status_badge(d.get("status","operational")),
                style="flex-shrink:0;"),
            cls="page-header", style="margin-bottom:14px;"
        ),
        # QR banner
        Div(
            Span("▣", style="font-size:1.3rem;"),
            Div(
                Div("Public QR page", style="font-size:0.75rem;font-weight:500;color:var(--c-primary);"),
                A(qr_url, href=qr_url, target="_blank",
                  style="font-size:0.8rem;color:var(--c-primary-md);font-family:monospace;"),
            ),
            style="display:flex;align-items:center;gap:12px;background:var(--c-primary-lt);border:1px solid #a7d9ce;border-radius:var(--r-md);padding:12px 16px;margin-bottom:20px;"
        ),
        # Device info
        Div(
            Div(
                H3("Device information", style="margin-bottom:12px;"),
                Dl(
                    *[Div(Dt(k, style="color:var(--c-text-3);font-weight:500;"), Dd(v),
                          style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--c-border);font-size:0.875rem;")
                      for k, v in [
                          ("Serial number", d.get("serial_number","—")),
                          ("Manufacturer",  d.get("manufacturer","—")),
                          ("Model",         d.get("model","—")),
                          ("Year",          str(d.get("manufacture_year","—"))),
                          ("Acquisition",   f"{d.get('acquisition_type','—')} · {fmt_date(d.get('acquisition_date',''))}"),
                          ("Location",      d.get("location","—")),
                          ("Organisation",  org.get("name","—")),
                      ]]
                ),
                cls="card"
            ),
            Div(
                H3("Maintenance", style="margin-bottom:12px;"),
                Dl(
                    *[Div(Dt(k, style="color:var(--c-text-3);font-weight:500;"), Dd(v),
                          style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--c-border);font-size:0.875rem;")
                      for k, v in [
                          ("Last maintenance", fmt_date(d.get("last_maintenance",""))),
                          ("Next maintenance", fmt_date(d.get("next_maintenance",""))),
                      ]]
                ),
                cls="card"
            ),
            cls="two-col", style="margin-bottom:16px;"
        ),
        # Maintenance logs
        Div(
            H3("Maintenance history", style="margin-bottom:12px;"),
            Div(
                Table(
                    Thead(Tr(Th("Date"), Th("Type"), Th("Description"), Th("Technician"), Th("Cost"))),
                    Tbody(*log_rows) if log_rows else Tbody(
                        Tr(Td("No maintenance logged yet.", colspan="5",
                               style="color:var(--c-text-3);padding:20px;text-align:center;")))
                ),
                style="border:none;border-radius:0;"
            ),
            cls="card", style="margin-bottom:16px;"
        ),
        # Fault reports
        Div(
            H3("Fault reports", style="margin-bottom:12px;"),
            Div(
                Table(
                    Thead(Tr(Th("Date"), Th("Reported by"), Th("Description"), Th("Severity"), Th("Status"))),
                    Tbody(*fault_rows) if fault_rows else Tbody(
                        Tr(Td("No fault reports.", colspan="5",
                               style="color:var(--c-text-3);padding:20px;text-align:center;")))
                ),
                style="border:none;border-radius:0;"
            ),
            cls="card"
        ),
    )

    return page_shell(content, current="/devices", title=f"{d.get('name','Device')} — FixMyMedTech")


# ══════════════════════════════════════════════════════════════
# PUBLIC QR PAGE
# ══════════════════════════════════════════════════════════════

@rt("/d/{device_id}")
async def get(req, device_id: str):
    try:
        data = await backend.get_device_public(device_id)
    except Exception:
        return pub_shell(
            Div(
                Div("⚠", style="font-size:2rem;display:block;margin-bottom:10px;"),
                H2("Device not found"),
                P("This QR code doesn't match any registered device."),
                style="text-align:center;padding:60px 24px;"
            )
        )

    d = data.get("device", {})
    docs = data.get("documents", [])
    faults = data.get("recent_faults", [])
    cat = d.get("device_categories") or {}

    nm = d.get("next_maintenance","")
    import datetime
    overdue = nm and nm < datetime.datetime.now().isoformat()

    doc_items = [
        A(
            Span("▶" if doc.get("type")=="video" else "📄" if doc.get("type")=="manual" else "📋",
                 style="font-size:1.2rem;"),
            Div(
                Div(doc.get("title",""), style="font-weight:500;font-size:0.875rem;"),
                Div(f"{doc.get('type','')} · {doc.get('language','').upper()}",
                    style="font-size:0.75rem;color:var(--c-text-3);"),
            ),
            href=doc.get("url","#"), target="_blank",
            style="display:flex;align-items:center;gap:10px;padding:10px;background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r-md);text-decoration:none;color:var(--c-text);margin-bottom:8px;"
        ) for doc in docs
    ]

    fault_items = [
        Div(
            Div(
                status_badge(f.get("severity","medium"), "severity"),
                status_badge(f.get("status","open"), "fault"),
                Span(fmt_date(f.get("reported_at","")),
                     style="font-size:0.72rem;color:var(--c-text-3);"),
                style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;"
            ),
            P(f.get("description",""), style="font-size:0.875rem;margin:0;"),
            style="background:var(--c-surface);border:1px solid var(--c-border);border-radius:var(--r-md);padding:12px;margin-bottom:8px;"
        ) for f in faults
    ]

    content = Div(
        # Header
        Div(
            Div(Span("✚", cls="pub-cross"), " FixMyMedTech", cls="pub-logo"),
            cls="pub-header"
        ),
        # Device identity
        Div(
            Div(cat.get("icon","🏥"), cls="dev-icon"),
            Div(
                Div(cat.get("name","Device"), cls="dev-cat"),
                Div(d.get("name",""), cls="dev-name"),
                Div(f"{d.get('manufacturer','')} · SN: {d.get('serial_number','')}".strip(" ·"),
                    cls="dev-meta"),
            ),
            Div(
                status_badge(d.get("status","operational")),
                Div(d.get("location",""), cls="dev-loc"),
                cls="dev-status"
            ),
            cls="device-identity"
        ),
        # Maintenance warning
        Div(
            Span("⚠", style="font-size:1rem;flex-shrink:0;"),
            Div(
                Strong("Maintenance overdue"),
                P(f"Due {fmt_date(nm)}. Contact your biomedical engineer."),
            ),
            cls="warn-bar"
        ) if overdue else "",
        # Report fault CTA
        Div(
            Div(
                Strong("Found a problem?", style="font-size:0.875rem;"),
                P("Report it to the biomed team.", style="font-size:0.8rem;margin:2px 0 0;"),
            ),
            A("⚠ Report fault", href=f"/d/{device_id}/report",
              cls="btn btn-danger btn-sm"),
            cls="report-cta"
        ),
        # Device info
        Div(
            H3("Device information",
               style="font-size:0.75rem;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--c-text-3);margin-bottom:8px;"),
            Dl(
                *[Div(Dt(k), Dd(v), cls="info-row")
                  for k, v in [
                      ("Status",       d.get("status","—")),
                      ("Location",     d.get("location","—")),
                      ("Manufacturer", d.get("manufacturer","—")),
                      ("Model",        d.get("model","—")),
                      ("Serial no.",   d.get("serial_number","—")),
                      ("Last maint.",  fmt_date(d.get("last_maintenance",""))),
                      ("Next maint.",  fmt_date(nm)),
                  ]],
                cls="info-list"
            ),
            cls="pub-section"
        ),
        # Manuals
        Div(
            H3("Manuals & documents",
               style="font-size:0.75rem;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--c-text-3);margin-bottom:8px;"),
            *doc_items if doc_items else [P("No documents attached.", style="color:var(--c-text-3);font-size:0.875rem;")],
            cls="pub-section"
        ) if docs else "",
        # Recent faults
        Div(
            H3("Recent fault reports",
               style="font-size:0.75rem;font-weight:500;text-transform:uppercase;letter-spacing:.04em;color:var(--c-text-3);margin-bottom:8px;"),
            *fault_items if fault_items else [P("No fault reports on record.", style="color:var(--c-text-3);font-size:0.875rem;")],
            cls="pub-section"
        ),
        # Footer
        Div("FixMyMedTech · Powered by CareAgain", cls="pub-footer"),
        cls="pub-page"
    )

    return pub_shell(content, title=f"{d.get('name','Device')} — FixMyMedTech")


# ══════════════════════════════════════════════════════════════
# PUBLIC FAULT REPORT
# ══════════════════════════════════════════════════════════════

@rt("/d/{device_id}/report")
async def get(req, device_id: str):
    content = Div(
        Div(Div(Span("✚", cls="pub-cross"), " FixMyMedTech", cls="pub-logo"), cls="pub-header"),
        Div(
            A("← Back to device", href=f"/d/{device_id}",
              style="font-size:0.875rem;color:var(--c-text-3);text-decoration:none;display:block;margin-bottom:16px;"),
            H2("Report a fault", style="margin-bottom:6px;"),
            P("No account needed. Your report goes directly to the biomed team.",
              style="margin-bottom:16px;"),
            Div(
                Label("Describe the problem *", cls="label"),
                Textarea(name="description", cls="input", rows="4",
                         placeholder="What is wrong with the device?"),
                cls="form-group"
            ),
            Div(
                Label("Severity", cls="label"),
                Div(
                    *[Label(Input(type="radio", name="severity", value=v,
                                  checked=(v=="medium")), f" {l}",
                             style="display:block;padding:8px 10px;border:1px solid var(--c-border);border-radius:var(--r-md);margin-bottom:6px;font-size:0.875rem;cursor:pointer;")
                      for v, l in [
                          ("low",      "Low — minor issue, device still usable"),
                          ("medium",   "Medium — needs attention"),
                          ("high",     "High — device partially unusable"),
                          ("critical", "Critical — device completely down"),
                      ]],
                )
            ),
            Div(
                Label("Your name (optional)", cls="label"),
                Input(name="reporter_name", cls="input", placeholder="Nurse / Technician name"),
                cls="form-group", style="margin-top:12px;"
            ),
            Button("Submit fault report", type="submit", cls="btn btn-primary",
                   style="width:100%;justify-content:center;margin-top:8px;"),
            style="padding:16px;"
        ),
        cls="pub-page",
        method="post", action=f"/d/{device_id}/report"
    )

    return pub_shell(
        Form(content, method="post", action=f"/d/{device_id}/report"),
        title="Report fault — FixMyMedTech"
    )


@rt("/d/{device_id}/report")
async def post(req, device_id: str, description: str,
               severity: str = "medium", reporter_name: str = ""):
    if not description.strip():
        return RedirectResponse(f"/d/{device_id}/report", status_code=302)

    try:
        await backend.submit_fault_public({
            "device_id": device_id,
            "description": description,
            "severity": severity,
            "reporter_name": reporter_name or "Anonymous",
        })
    except Exception:
        pass

    return pub_shell(
        Div(
            Div(Div(Span("✚", cls="pub-cross"), " FixMyMedTech", cls="pub-logo"), cls="pub-header"),
            Div(
                Div("✓", style="width:52px;height:52px;background:var(--c-green-lt);color:var(--c-green);border-radius:50%;font-size:1.3rem;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;"),
                H2("Report submitted"),
                P("A technician will be notified. Thank you for helping keep this equipment working."),
                A("← Back to device", href=f"/d/{device_id}",
                  cls="btn btn-secondary", style="margin-top:16px;"),
                style="text-align:center;padding:40px 24px;"
            ),
            cls="pub-page"
        )
    )


# ── Root redirect ─────────────────────────────────────────────
@rt("/")
async def get(req):
    return RedirectResponse(
        "/dashboard" if get_token(req) else "/login",
        status_code=302
    )


serve()