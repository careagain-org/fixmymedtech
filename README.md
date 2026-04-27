# FixMyMedTech — Architecture Guide

Medical equipment management platform for LMICs (Low and Middle Income Countries).

**Stack:** FastAPI (REST backend) + FastHTML (frontend) + Supabase (database & auth)

---

## Architecture overview

```
Browser
  │
  ▼
FastHTML (port 5000)          ← renders HTML pages, handles sessions
  │  httpx async requests
  ▼
FastAPI (port 8000)           ← REST API, business logic, auth validation
  │  supabase-py
  ▼
Supabase (PostgreSQL)         ← database, auth, file storage
```

FastHTML is not a traditional frontend — it is a Python web server that generates HTML server-side. There is no JavaScript framework, no build step, and no API calls from the browser. The browser talks only to FastHTML. FastHTML talks to FastAPI. FastAPI talks to Supabase.

Authentication uses Supabase JWT tokens stored in **server-side sessions** (cookies). The token never touches the browser directly.

---

## Project structure

```
fixmymedtech/
│
├── backend/                        ← FastAPI REST API
│   ├── main.py                     ← App entry point, CORS, router registration
│   ├── deps.py                     ← Auth helpers, get_current_user
│   ├── requirements.txt
│   ├── .env.example
│   └── routers/
│       ├── auth.py                 ← POST /api/auth/login, /signup, /logout
│       ├── devices.py              ← CRUD /api/devices + public QR endpoint
│       ├── fault_reports.py        ← Fault submission and management
│       └── dashboard.py            ← Aggregated stats
│
├── frontend/                       ← FastHTML frontend server
│   ├── main.py                     ← All routes and page rendering
│   ├── api.py                      ← HTTP client (calls FastAPI via httpx)
│   ├── components.py               ← Reusable UI components, page shells
│   ├── requirements.txt
│   ├── .env.example
│   └── static/
│       ├── styles.css              ← All CSS — edit this to change the design
│       └── *.png / *.svg           ← Images and icons
│
├── supabase/
│   └── schema.sql                  ← Run once in Supabase SQL Editor
│
├── docs/                           ← MkDocs documentation
│   ├── mkdocs.yml
│   └── docs/*.md
│
└── docker-compose.yml              ← Runs all services together
```

---

## Key design decisions

### Why two servers?

FastHTML handles routing and rendering. FastAPI handles data and business logic. This separation means:

- The API can be used independently by mobile apps or third parties later
- Backend logic stays in FastAPI where it is easier to test
- FastHTML stays thin — it only fetches data and renders HTML

### Why server-side sessions?

JWT tokens are stored in encrypted server-side sessions (cookies), not in localStorage or the browser. This is more secure — the token is never exposed to JavaScript or visible in the browser.

### Why Supabase?

Supabase provides PostgreSQL, authentication, file storage, and row-level security in one managed service. Row Level Security (RLS) ensures each hospital can only see its own devices and data, enforced at the database level.

---

## User roles

| Role | What they can do |
|------|-----------------|
| `clinical_staff` | Scan QR codes, view device info, report faults |
| `technician` | All of the above + update device status, log maintenance |
| `admin` | All of the above + create/delete devices, manage users |

---

## Page map

| URL | Auth | Who | What |
|-----|------|-----|------|
| `/login` | No | Anyone | Sign in |
| `/signup` | No | Anyone | Create account |
| `/dashboard` | Yes | Admin / Technician | Stats overview |
| `/devices` | Yes | Admin / Technician | Device list with filters |
| `/devices/new` | Yes | Admin / Technician | Register new device |
| `/devices/{id}` | Yes | Admin / Technician | Device detail, history, faults |
| `/d/{id}` | **No** | Anyone with QR | Public device page |
| `/d/{id}/report` | **No** | Anyone with QR | Submit fault report |

---

## Data flow — QR scan (no login)

```
1. Nurse scans QR on device
2. Browser opens: https://yourdomain.com/d/{device_id}
3. FastHTML calls: GET {API_URL}/api/devices/public/{device_id}
4. FastAPI queries Supabase (no auth required for this endpoint)
5. FastHTML renders device info, manuals, fault report form
6. Nurse submits fault → FastHTML calls POST /api/faults/public
7. FastAPI updates Supabase, device status changes to "fault" if critical
```

## Data flow — admin login

```
1. Admin submits login form
2. FastHTML calls: POST {API_URL}/api/auth/login
3. FastAPI calls Supabase Auth → gets JWT token
4. FastHTML stores token in encrypted session cookie
5. All subsequent requests include token in Authorization header (server-side)
6. FastAPI validates token on every protected endpoint via Depends(get_current_user)
```

---

## Local development setup

### 1. Supabase

1. Create a project at https://supabase.com
2. Go to **SQL Editor** → paste and run `supabase/schema.sql`
3. Go to **Authentication → Settings** → disable email confirmation for development
4. Go to **Project Settings → API** → copy your keys

### 2. Backend (FastAPI)

```bash
cd backend
cp .env.example .env
# Edit .env:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=sb_secret_xxx
# SUPABASE_ANON_KEY=sb_publishable_xxx
# FRONTEND_URL=http://localhost:5001

pip install -r requirements.txt
uvicorn main:app --reload --port 8888

# API runs at:  {API_URL}
# Swagger docs: {API_URL}/docs
```

### 3. Frontend (FastHTML)

```bash
cd frontend
cp .env.example .env
# Edit .env:
# API_URL=http://localhost:8888
# SESSION_SECRET=any-random-string

pip install -r requirements.txt
python main.py

# App runs at: http://localhost:5000
```

### 4. Documentation (MkDocs)

```bash
cd docs
pip install mkdocs-material
mkdocs serve

# Docs at: http://localhost:8080
```

---

## Production deploy

### With Docker Compose (recommended)

```bash
cp .env.example .env
# Fill in all values

docker compose up --build -d
```

Services will be available at:

| Service | URL |
|---------|-----|
| Frontend (FastHTML) | |
| Backend (FastAPI) | |
| API docs |  |
| Documentation |  |

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `sb_secret_xxx` — bypasses RLS, backend only |
| `SUPABASE_ANON_KEY` | `sb_publishable_xxx` — for token validation |
| `FRONTEND_URL` | FastHTML URL for CORS (e.g. `http://localhost:5000`) |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `API_URL` | FastAPI URL (e.g. `http://localhost:8000`) |
| `SESSION_SECRET` | Random string for encrypting session cookies |

---

## QR codes

Each device gets a permanent public URL:

```
https://yourdomain.com/d/{device_id}
```

The UUID never changes. The content behind it updates in the database. To generate a printable QR label:

1. Go to https://qr.io or https://www.qrcode-monkey.com
2. Enter the device URL
3. Download as SVG or PNG
4. Print on water-resistant label and attach to device

---
