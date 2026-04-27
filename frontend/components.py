# components.py — reusable FastHTML UI components

from fasthtml.common import *


# ── Design tokens ────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

:root {
  --font-body:
		Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell,
		'Open Sans', 'Helvetica Neue', sans-serif;
	--font-mono: 'Fira Mono', monospace;
	--color-bg-0: rgb(202, 216, 228);
	--color-bg-1: hsl(204, 33%, 94%);
	--color-bg-2: hsl(224, 44%, 95%);
	--color-theme-1: #01a2b5;
	--color-theme-2: #104f84;
	--color-text: rgba(0, 0, 0, 0.7);
	--column-width: 42rem;
	--column-margin-top: 4rem;
	font-family: var(--font-body);
	color: var(--color-text);
  --c-bg:        #f4f3ee;
  --c-bg-2:      #eceae2;
  --c-surface:   #ffffff;
  --c-border:    #d6d3c9;
  --c-primary: #104f84;
  --c-primary-lt: #d4ece5;
  --c-primary-mid: #01a2b5;
  --c-text:      #1a1916;
  --c-text-2:    #4a4740;
  --c-text-3:    #8a8780;
  --c-green:     #16a34a;
  --c-green-lt:  #dcfce7;
  --c-amber:     #d97706;
  --c-amber-lt:  #fef3c7;
  --c-red:       #dc2626;
  --c-red-lt:    #fee2e2;
  --c-blue:      #2563eb;
  --c-blue-lt:   #dbeafe;
  --font-display:'DM Serif Display', Georgia, serif;
  --font-body:   'DM Sans', system-ui, sans-serif;
  --r-md: 10px; --r-lg: 16px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-body); background: var(--c-bg); color: var(--c-text); -webkit-font-smoothing: antialiased; }
h1,h2,h3 { font-family: var(--font-display); line-height: 1.2; }
h1 { font-size: 1.8rem; } h2 { font-size: 1.3rem; } h3 { font-size: 1.05rem; }
p { color: var(--c-text-2); font-size: 0.9rem; line-height: 1.7; }
a { color: var(--c-primary); text-decoration: none; }

/* App shell */
.shell { display: flex; min-height: 100vh; }
.sidebar { width: 210px; flex-shrink: 0; background: var(--c-primary); display: flex; flex-direction: column; position: fixed; top:0; left:0; bottom:0; z-index:100; }
.sb-logo { display:flex; align-items:center; gap:8px; padding:20px 16px; border-bottom:1px solid rgba(255,255,255,0.1); }
.sb-cross { color:#5eead4; font-size:1.2rem; }
.sb-name { font-family:var(--font-display); font-size:1.2rem; color:#fff; }
.sb-nav { flex:1; padding:14px 10px; display:flex; flex-direction:column; gap:3px; }
.nav-link { display:flex; align-items:center; gap:8px; padding:8px 10px; border-radius:var(--r-md); font-size:0.875rem; font-weight:500; color:rgba(255,255,255,0.6); text-decoration:none; transition:all .15s; }
.nav-link:hover,.nav-link.active { background:rgba(255,255,255,0.15); color:#fff; }
.sb-foot { padding:12px 10px; border-top:1px solid rgba(255,255,255,0.1); font-size:0.75rem; color:rgba(255,255,255,0.5); }
.main { margin-left:210px; flex:1; padding:28px 32px; }

/* Buttons */
.btn { display:inline-flex; align-items:center; gap:6px; padding:9px 18px; border-radius:var(--r-md); font-family:var(--font-body); font-size:0.875rem; font-weight:500; cursor:pointer; transition:all .15s; border:none; text-decoration:none; }
.btn-primary { background:var(--c-primary); color:#fff; }
.btn-primary:hover { background:var(--c-primary-md); }
.btn-secondary { background:var(--c-bg-2); color:var(--c-text); border:1px solid var(--c-border); }
.btn-danger { background:var(--c-red-lt); color:var(--c-red); border:1px solid #fca5a5; }
.btn-sm { padding:5px 12px; font-size:0.8rem; }

/* Cards */
.card { background:var(--c-surface); border:1px solid var(--c-border); border-radius:var(--r-lg); padding:18px 20px; }

/* Badges */
.badge { display:inline-flex; align-items:center; padding:2px 9px; border-radius:20px; font-size:0.75rem; font-weight:500; }
.badge-green { background:var(--c-green-lt); color:var(--c-green); }
.badge-amber { background:var(--c-amber-lt); color:var(--c-amber); }
.badge-red   { background:var(--c-red-lt);   color:var(--c-red);   }
.badge-blue  { background:var(--c-blue-lt);  color:var(--c-blue);  }
.badge-gray  { background:var(--c-bg-2);     color:var(--c-text-3);}

/* Forms */
.input { width:100%; padding:9px 13px; border:1px solid var(--c-border); border-radius:var(--r-md); font-family:var(--font-body); font-size:0.875rem; background:var(--c-surface); color:var(--c-text); }
.input:focus { outline:none; border-color:var(--c-primary); box-shadow:0 0 0 3px var(--c-primary-lt); }
.label { display:block; font-size:0.8rem; font-weight:500; color:var(--c-text-2); margin-bottom:5px; }
.form-group { margin-bottom:14px; }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }

/* Tables */
.table-wrap { overflow-x:auto; border:1px solid var(--c-border); border-radius:var(--r-lg); }
table { width:100%; border-collapse:collapse; font-size:0.875rem; }
th { text-align:left; padding:10px 14px; font-size:0.75rem; font-weight:600; letter-spacing:.05em; text-transform:uppercase; color:var(--c-text-3); background:var(--c-bg); border-bottom:1px solid var(--c-border); }
td { padding:11px 14px; border-bottom:1px solid var(--c-border); color:var(--c-text-2); }
tr:last-child td { border-bottom:none; }
tr:hover td { background:var(--c-bg); }

/* Alerts */
.alert { padding:11px 14px; border-radius:var(--r-md); font-size:0.875rem; margin-bottom:14px; }
.alert-error   { background:var(--c-red-lt);   color:var(--c-red);   border:1px solid #fca5a5; }
.alert-success { background:var(--c-green-lt); color:var(--c-green); border:1px solid #86efac; }
.alert-warning { background:var(--c-amber-lt); color:var(--c-amber); border:1px solid #fcd34d; }

/* Stats grid */
.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:20px; }
.stat-card { background:var(--c-surface); border:1px solid var(--c-border); border-radius:var(--r-lg); padding:16px 18px; }
.stat-label { font-size:0.72rem; font-weight:500; color:var(--c-text-3); text-transform:uppercase; letter-spacing:.04em; margin-bottom:5px; }
.stat-num { font-family:var(--font-display); font-size:2rem; color:var(--c-text); line-height:1; }
.stat-sub { font-size:0.72rem; color:var(--c-text-3); margin-top:3px; }
.stat-card.g { border-top:3px solid var(--c-green); }
.stat-card.a { border-top:3px solid var(--c-amber); }
.stat-card.r { border-top:3px solid var(--c-red); }

/* Two col */
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.page-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:22px; }

/* Toolbar */
.toolbar { display:flex; align-items:center; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.pill { padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:500; background:var(--c-surface); border:1px solid var(--c-border); color:var(--c-text-2); cursor:pointer; text-decoration:none; }
.pill.active { background:var(--c-primary); color:#fff; border-color:var(--c-primary); }

/* Public QR page */
.pub-page { max-width:520px; margin:0 auto; min-height:100vh; display:flex; flex-direction:column; background:var(--c-bg); }
.pub-header { background:var(--c-primary); padding:12px 16px; display:flex; align-items:center; justify-content:space-between; }
.pub-logo { display:flex; align-items:center; gap:7px; color:#fff; font-family:var(--font-display); font-size:1rem; }
.pub-cross { color:#5eead4; }
.device-identity { display:flex; align-items:flex-start; gap:12px; padding:16px; background:var(--c-surface); border-bottom:1px solid var(--c-border); }
.dev-icon { font-size:2rem; flex-shrink:0; }
.dev-cat { font-size:0.72rem; color:var(--c-text-3); text-transform:uppercase; letter-spacing:.04em; }
.dev-name { font-size:1.2rem; font-family:var(--font-display); margin:2px 0; }
.dev-meta { font-size:0.78rem; color:var(--c-text-3); }
.dev-status { flex-shrink:0; text-align:right; }
.dev-loc { font-size:0.72rem; color:var(--c-text-3); margin-top:4px; }
.warn-bar { display:flex; gap:8px; align-items:flex-start; background:var(--c-amber-lt); border-left:4px solid var(--c-amber); padding:11px 14px; font-size:0.85rem; color:var(--c-amber); }
.warn-bar p { color:#92400e; font-size:0.78rem; margin:2px 0 0; }
.report-cta { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:var(--c-surface); border-bottom:1px solid var(--c-border); }
.pub-tabs { display:flex; background:var(--c-surface); border-bottom:1px solid var(--c-border); margin-top:6px; }
.pub-tab { flex:1; padding:10px 6px; font-size:0.85rem; font-weight:500; color:var(--c-text-3); background:none; border:none; cursor:pointer; border-bottom:2px solid transparent; text-align:center; text-decoration:none; }
.pub-tab.active { color:var(--c-primary); border-bottom-color:var(--c-primary); }
.info-list { display:flex; flex-direction:column; padding:8px 16px; }
.info-row { display:flex; justify-content:space-between; padding:9px 0; border-bottom:1px solid var(--c-border); font-size:0.875rem; }
.info-row:last-child { border-bottom:none; }
.info-row dt { color:var(--c-text-3); font-weight:500; }
.info-row dd { color:var(--c-text); font-weight:500; }
.pub-section { padding:14px 16px; }
.pub-footer { margin-top:auto; padding:16px; text-align:center; border-top:1px solid var(--c-border); font-size:0.75rem; color:var(--c-text-3); }

/* Login / Signup */
.auth-wrap { min-height:100vh; display:grid; grid-template-columns:440px 1fr; }
.auth-card { padding:48px 40px; display:flex; flex-direction:column; justify-content:center; background:var(--c-surface); border-right:1px solid var(--c-border); }
.auth-brand { margin-bottom:28px; }
.brand-icon { font-size:1.8rem; color:var(--c-primary); display:block; margin-bottom:8px; }
.auth-bg { background:var(--c-primary); display:flex; align-items:flex-end; padding:48px; position:relative; overflow:hidden; }
.auth-bg::before { content:''; position:absolute; inset:0; background:radial-gradient(circle at 20% 30%, rgba(94,234,212,0.12) 0%, transparent 50%); }
.auth-quote { position:relative; font-family:var(--font-display); font-size:1.5rem; color:rgba(255,255,255,0.9); line-height:1.5; border-left:3px solid #5eead4; padding-left:20px; }
.auth-quote em { color:#5eead4; }
.auth-link { margin-top:14px; font-size:0.82rem; color:var(--c-text-3); text-align:center; }
.auth-link a { color:var(--c-primary); font-weight:500; }

/* Overdue */
.overdue { color:var(--c-red); font-weight:500; }
.overdue-tag { display:inline-block; margin-left:3px; background:var(--c-red-lt); color:var(--c-red); font-size:0.7rem; padding:1px 5px; border-radius:10px; }

@media (max-width:768px) {
  .shell { flex-direction:column; }
  .sidebar { position:relative; width:100%; height:auto; }
  .main { margin-left:0; padding:16px; }
  .stat-grid { grid-template-columns:1fr 1fr; }
  .two-col { grid-template-columns:1fr; }
  .auth-wrap { grid-template-columns:1fr; }
  .auth-bg { display:none; }
  .auth-card { padding:32px 20px; }
  .form-row { grid-template-columns:1fr; }
}
"""


def status_badge(status: str, type: str = "device"):
    device_map = {
        "operational":    ("Operational",   "badge-green"),
        "maintenance":    ("Maintenance",    "badge-amber"),
        "fault":          ("Fault",          "badge-red"),
        "decommissioned": ("Decommissioned", "badge-gray"),
    }
    fault_map = {
        "open":        ("Open",        "badge-red"),
        "assigned":    ("Assigned",    "badge-amber"),
        "in_progress": ("In Progress", "badge-blue"),
        "resolved":    ("Resolved",    "badge-green"),
    }
    severity_map = {
        "low":      ("Low",      "badge-gray"),
        "medium":   ("Medium",   "badge-amber"),
        "high":     ("High",     "badge-red"),
        "critical": ("Critical", "badge-red"),
    }
    m = fault_map if type == "fault" else severity_map if type == "severity" else device_map
    label, cls = m.get(status, (status, "badge-gray"))
    return Span(label, cls=f"badge {cls}")


def sidebar(current: str = ""):
    links = [
        ("/dashboard", "◈", "Dashboard"),
        ("/devices",   "⊞", "Devices"),
        ("/logout",   "➜]", "Logout"),
    ]
    return Aside(
        Div(Span("✚", cls="sb-cross"), Span("FixMyMedTech", cls="sb-name"), cls="sb-logo"),
        Nav(
            *[A(Span(icon), f" {label}", href=href,
                cls=f"nav-link {'active' if current == href else ''}")
              for href, icon, label in links],
            cls="sb-nav"
        ),
        cls="sidebar"
    )


def page_shell(content, current: str = "", title: str = "FixMyMedTEch"):
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title(title),
            Style(CSS),
        ),
        Body(
            Div(
                sidebar(current),
                Main(content, cls="main"),
                cls="shell"
            )
        )
    )


def pub_shell(content, title: str = "FixMyMedTech"):
    """Shell for public QR pages — no sidebar."""
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title(title),
            Style(CSS),
        ),
        Body(content)
    )


def alert(message: str, type: str = "error"):
    return Div(message, cls=f"alert alert-{type}") if message else ""


def fmt_date(iso: str) -> str:
    if not iso:
        return "—"
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y")
    except Exception:
        return iso[:10]