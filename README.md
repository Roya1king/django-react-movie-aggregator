# Django + React Movie Aggregator (Monorepo)

A full‑stack, real‑time movie scraper and aggregator with:
- Backend: Django, Django Channels (WebSockets), Celery, Redis
- Frontend: React (Vite + Tailwind)
- Scraping: requests/BeautifulSoup and a profile‑based browser lane (Selenium/Playwright) for Cloudflare‑protected sites

This root README brings together the essentials from both the backend and frontend READMEs so you can set up and run everything end‑to‑end.

## Monorepo layout

```
.
├── backend/            # Django app (Channels, Celery workers, admin, tasks)
│   ├── manage.py
│   ├── requirements.txt
│   ├── scraper_project/
│   └── scraper_api/
└── frontend/           # React (Vite) app
    ├── src/
    ├── public/
    ├── package.json
    └── vite.config.js
```

## Prerequisites

- Windows PowerShell (these instructions use PS syntax)
- Python 3.10+
- Node.js 16+ (or current LTS)
- Docker Desktop (recommended) for Redis
- Brave Browser (installed in the default location) for Selenium profile warm‑up

## 1) Start Redis

Run Redis in a container (recommended):

```powershell
# Terminal A (any folder)
docker run -d -p 6379:6379 redis
```

## 2) Backend setup (Django)

```powershell
# Terminal B
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# Optional (if you use Selenium-based scrapers)
pip install selenium-stealth webdriver-manager

# Initialize DB and admin
python manage.py migrate
python manage.py createsuperuser
```

Optional: one‑time “profile warm‑up” for Cloudflare‑heavy sites (Selenium + Brave). Make sure all Brave windows are closed before running:

```powershell
python train_profile.py
# A Brave window opens. Log in to Google, visit target sites, solve CAPTCHAs, then Ctrl+C to stop.
```

## 3) Frontend setup (React + Vite)

```powershell
# Terminal C
cd frontend
npm install
```

Build once if you want Django to serve the compiled SPA (no separate Vite server):

```powershell
npm run build
# Outputs: frontend/dist (can be served by Django in production)
```

## 4) Run the project

You have two ways to run the UI during development:

### A) Integrated mode — Django serves the built React app (3 backend terminals)

This is simplest when you’ve built the frontend (`npm run build`). Make sure Redis is running.

```powershell
# Terminal 1 — Fast lane worker (backend)
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker --pool=threads -Q fast_queue -c 12 --loglevel=info
```

```powershell
# Terminal 2 — Profile lane worker (backend)
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker --pool=threads -Q profile_queue -c 1 --loglevel=info
```

```powershell
# Terminal 3 — ASGI server (backend)
cd backend
.\venv\Scripts\activate
daphne -p 8000 scraper_project.asgi:application
```

Now visit:
- App: http://localhost:8000
- Admin: http://localhost:8000/admin

Tip: Ensure your Django `TEMPLATES["DIRS"]` and static configuration are pointed at the built frontend if you’re serving `frontend/dist`.

### B) Dev mode — Run Vite dev server (4 terminals)

You’ll run four processes:

- Fast lane Celery worker (simple HTTP scrapers)
- Profile lane Celery worker (Selenium/Playwright; concurrency 1)
- ASGI server (Daphne)
- Vite dev server (frontend)

```powershell
# Terminal B — Fast lane worker (backend)
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker -Q fast_queue -c 10 --pool=threads --loglevel=info
```

```powershell
# Terminal D — Profile lane worker (backend)
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker -Q profile_queue -c 1 --pool=threads --loglevel=info
```

```powershell
# Terminal E — ASGI server (backend)
cd backend
.\venv\Scripts\activate
daphne -p 8000 scraper_project.asgi:application
```

```powershell
# Terminal C — Frontend dev server
cd frontend
npm run dev
```

- Frontend: http://localhost:5173
- Backend (HTTP/WS): http://localhost:8000
- Django Admin: http://localhost:8000/admin/

---

## One‑time Selenium profile warm‑up (CRITICAL)

To reliably bypass Cloudflare on protected sites, warm a persistent Brave profile:

```powershell
# Close all Brave windows first
cd backend
.\venv\Scripts\activate
python train_profile.py
```

In the Brave window that opens (your bot profile):
- Sign in to Google at https://google.com
- Visit and solve CAPTCHAs for each protected site you plan to scrape (e.g., https://hdhub4u.pictures/, https://vegamovies.gripe/, https://vegamovies.talk/)
When done, close the window and stop the script (CTRL + C).

## WebSocket contract (search)

- Endpoint: `ws://localhost:8000/ws/search/`
- Client → Server (start a search):

```json
{ "action": "search", "term": "your movie" }
```

- Server → Client (result):

```json
{ "source": "SiteName", "title": "Movie Title", "link": "https://...", "poster": "https://..." }
```

- Server → Client (error):

```json
{ "error": true, "message": "Failed to fetch data from ..." }
```

## Admin: Site configuration

In Django Admin → Site Sources, define per‑site settings:
- Base URL, active flag
- Search method (GET/POST) + endpoint (use %QUERY%)
- Whether a full browser is required (Selenium/Playwright)
- CSS selectors for result container, title, link, poster, and the attribute that holds image URLs

### Example: HDHub4u1

- Name: `HDHub4u1`
- Base URL: `https://hdhub4u.pictures`
- Search type: `GET Parameter`
- Search endpoint: `/?s=%QUERY%`
- Requires playwright: checked (routes to Selenium `profile_queue`)
- Result container selector: `li.thumb`
- Result title selector: `figcaption a p`
- Result link selector: `figcaption a`
- Result poster selector: `figure img`
- Result poster attribute: `src`

### Example: Vegamovies.talk

- Name: `Vegamovies.talk`
- Base URL: `https://vegamovies.talk`
- Search type: `POST API`
- Search endpoint: `/`
- Post payload template:

```
do=search
subaction=search
story=%QUERY%
```

- Requires playwright: checked
- Result container selector: `article.post-item`
- Result title selector: `h3.entry-title a`
- Result link selector: `h3.entry-title a`
- Result poster selector: `img.blog-picture`
- Result poster attribute: `src`

### Example: Vegamovies.gripe

- Name: `Vegamovies`
- Base URL: `https://vegamovies.gripe`
- Search type: `GET Parameter`
- Search endpoint: `/?s=%QUERY%`
- Requires playwright: checked
- Result container selector: `article.grid-item`
- Result title selector: `h2.post-title a`
- Result link selector: `h2.post-title a`
- Result poster selector: `img.wp-post-image`
- Result poster attribute: `src`

## Environment variables (suggested)

Consider using .env files for local secrets:

```
# backend/.env (example)
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace-me
ALLOWED_HOSTS=127.0.0.1,localhost
REDIS_URL=redis://127.0.0.1:6379/0
```

```
# frontend/.env (example)
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/search/
```

Your repo’s root .gitignore already ignores `.env` files but allows `*.example` variants. If you want, we can add `backend/.env.example` and `frontend/.env.example` for onboarding.

## Troubleshooting

- Selenium scrapers fail instantly → ensure you ran `train_profile.py` with all Brave windows closed and solved CAPTCHAs for protected sites.
- Profile queue crashing/locking → keep `profile_queue` at `-c 1` (single concurrency).
- Import errors for `daphne`/`channels` → verify your virtualenv is activated in every backend terminal.
- Redis connection errors → make sure the container is running and listening on 6379.

## Useful scripts

Backend (from `backend/`):
- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Admin superuser: `python manage.py createsuperuser`

Frontend (from `frontend/`):
- Dev: `npm run dev`
- Build: `npm run build` (outputs to `frontend/dist/`)
- Preview: `npm run preview`

---

For production, review security settings (SECRET_KEY rotation, ALLOWED_HOSTS), configure a production ASGI server, and consider Docker Compose to wire Redis, Django, workers, and the frontend together. If you’d like, I can add a `docker-compose.yml` and `.env.example` files to streamline local and prod setups.