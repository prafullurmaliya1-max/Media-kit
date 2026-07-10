# Creator Media Kit Dashboard

A live, shareable analytics dashboard for content creators.
Connects to YouTube + Instagram APIs and generates a public link brands can view.

## Project structure

```
mediakit/
├── backend/               ← FastAPI (Python)
│   ├── main.py            ← App entry point
│   ├── models.py          ← Database table definitions
│   ├── database.py        ← PostgreSQL connection
│   ├── cache.py           ← Cache freshness logic
│   ├── requirements.txt   ← Python packages
│   ├── Dockerfile
│   └── routes/
│       ├── auth.py        ← Google OAuth
│       ├── youtube.py     ← YouTube Data API v3
│       ├── instagram.py   ← Instagram Graph API
│       └── profile.py     ← Public kit + rates
├── frontend/              ← Next.js (React)
│   ├── pages/
│   │   ├── index.js       ← Landing page
│   │   ├── dashboard.js   ← Creator dashboard (private)
│   │   └── kit/[slug].js  ← Public media kit (for brands)
│   ├── lib/api.js         ← All API calls
│   └── package.json
├── docker-compose.yml     ← Runs backend + postgres together
└── .gitignore
```

---

## Setup — Phase 1 (local dev)

### Step 1: Clone and install

```bash
git clone <your-repo>
cd mediakit
```

### Step 2: Set up backend environment

```bash
cd backend
cp .env.example .env
# Now open .env and fill in your API keys (see below)
```

### Step 3: Get your API keys

**Google OAuth + YouTube API:**
1. Go to console.cloud.google.com
2. Create a new project → "APIs & Services" → "Credentials"
3. Create OAuth 2.0 Client ID → Web Application
4. Add authorized redirect URI: `http://localhost:8000/auth/callback`
5. Enable "YouTube Data API v3" in the APIs library
6. Copy Client ID + Secret into .env

**Instagram Graph API:**
1. Go to developers.facebook.com
2. Create a new app → "Consumer"
3. Add Instagram Basic Display product
4. Copy App ID + Secret into .env

### Step 4: Start the backend + database

```bash
# From the root mediakit/ folder
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- FastAPI on port 8000

Test it: open http://localhost:8000/health — should return `{"status": "ok"}`
See all routes: http://localhost:8000

### Step 5: Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

### Step 6: Test the full flow

1. Open http://localhost:3000
2. Click "Connect YouTube" → Google login → authorize → lands on dashboard
3. Dashboard shows your real YouTube stats
4. Open http://localhost:3000/kit/yourname — this is the public shareable page

---

## API endpoints

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | /health | Health check |
| GET | /auth/google | Start Google OAuth |
| GET | /auth/callback | OAuth callback |
| GET | /auth/me?user_id=xxx | Get logged-in user |
| GET | /youtube/stats/{user_id} | YouTube stats (cached) |
| GET | /instagram/connect | Start Instagram OAuth |
| GET | /instagram/stats/{user_id} | Instagram stats (cached) |
| PATCH | /profile/{user_id} | Update bio/location/etc |
| PUT | /profile/{user_id}/rates | Update sponsorship rates |
| GET | /profile/kit/{slug} | Public kit data |

---

## Next steps (Phase 2+)

- Phase 2: Wire up real YouTube API calls with token refresh
- Phase 3: Instagram advanced insights (reel views, story reach)
- Phase 4: Deploy to Render (backend) + Vercel (frontend)
- Phase 5: Custom domain for shareable links
 
