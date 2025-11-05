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
pip install selenium-stealth

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

## 4) Run the full stack (4 terminals)

You’ll typically run four processes:

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