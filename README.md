# MedTrack QR — Setup Guide

Medical equipment management platform for LMICs.
Stack: FastAPI + Supabase + SvelteKit PWA

---

## Project structure

```
medtrack/
├── supabase/
│   └── schema.sql          ← Run this in Supabase SQL editor
├── backend/
│   ├── main.py             ← FastAPI app entry point
│   ├── deps.py             ← Auth helpers
│   ├── requirements.txt
│   ├── .env.example        ← Copy to .env and fill in keys
│   └── routers/
│       ├── auth.py         ← Login / signup
│       ├── devices.py      ← Device CRUD + public QR endpoint
│       ├── fault_reports.py← Fault report submission + management
│       └── dashboard.py    ← Aggregated stats
└── frontend/
    ├── src/
    │   ├── routes/
    │   │   ├── +layout.svelte       ← App shell with sidebar
    │   │   ├── login/+page.svelte   ← Login page
    │   │   ├── dashboard/+page.svelte
    │   │   ├── devices/
    │   │   │   ├── +page.svelte     ← Device list
    │   │   │   ├── new/+page.svelte ← Add device form
    │   │   │   └── [id]/+page.svelte← Device detail (admin)
    │   │   └── d/
    │   │       └── [id]/+page.svelte← PUBLIC QR page (no auth)
    │   ├── lib/
    │   │   ├── api/client.js        ← API client
    │   │   ├── stores/auth.js       ← Auth store
    │   │   └── components/
    │   │       └── StatusBadge.svelte
    │   └── app.css                  ← Design system
    ├── svelte.config.js
    └── vite.config.js               ← PWA config
```

---

## 1. Supabase setup

1. Create a project at https://supabase.com
2. Go to **SQL Editor** → paste and run `supabase/schema.sql`
3. Go to **Project Settings → API** → copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

---

## 2. Backend setup

```bash
cd backend
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY

pip install -r requirements.txt
uvicorn main:app --reload
# API runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

## 3. Frontend setup

```bash
cd frontend
cp .env.example .env
# Set PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
# Runs at http://localhost:5173
```

---

## 4. Production deploy (your server)

### Backend (with systemd or supervisor)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Frontend (build static files)

```bash
npm run build
# Outputs to frontend/build/
```

### Nginx config

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend PWA
    location / {
        root /path/to/medtrack/frontend/build;
        try_files $uri $uri/ /index.html;
        # Long cache for static assets
        location ~* \.(js|css|png|jpg|ico|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 5. QR codes

Each device gets a permanent URL: `https://yourdomain.com/d/{device_id}`

To generate a printable QR:

- Use https://qr.io or https://www.qrcode-monkey.com
- Enter the device URL
- Download as SVG/PNG
- Print on water-resistant label and attach to device

The URL never changes. The content behind it updates in the database.

---

## Key flows

| Who                        | What                                             | URL                         |
| -------------------------- | ------------------------------------------------ | --------------------------- |
| Nurse / technician (field) | Scan QR → see device info, manuals, report fault | `/d/{id}` — no login needed |
| Hospital admin             | Dashboard, manage devices, see faults            | `/dashboard`, `/devices`    |
| Biomedical engineer        | Update device status, log maintenance            | `/devices/{id}`             |

---

## Offline behaviour (PWA)

- Device pages (`/d/{id}`) are cached by the Service Worker after first visit
- Manuals/PDFs cached for 30 days
- API responses cached for 7 days
- Fault reports require internet connection to submit
