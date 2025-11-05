# Personal Movie Scraper Aggregator

This repository contains a full-stack, real-time movie scraper and aggregator. It uses a React (Vite) frontend and a Django backend with Django Channels for WebSocket streaming and Celery for background scraping tasks.

The project is designed to be resilient and fast by using two Celery "lanes" (queues): a high-speed lane for simple HTTP scrapers and a profile-locked lane for Selenium-based scrapers that need a warmed browser profile.

## Core Features

- Real-time results streamed to the frontend via WebSockets (Django Channels).
- Dynamic admin panel (Django Admin) for adding, editing and removing target sites and CSS selectors.
- Multi-site parallel scraping with per-site configuration.
- Two Celery queues for robust concurrency:
  - `fast_queue` for lightweight HTTP scrapers (high concurrency).
  - `profile_queue` for Selenium (Brave) scrapers (concurrency = 1 to avoid profile lock conflicts).
- Cloudflare bypass support using Selenium + selenium-stealth and a warmed, persistent Brave profile.

## Tech Stack

- Frontend: React (Vite), Tailwind CSS
- Backend: Django, Django Channels (ASGI)
- Task queue: Celery
- Broker / Cache: Redis
- Scraping: BeautifulSoup, requests, Selenium, webdriver-manager, selenium-stealth
- ASGI server: Daphne

## Architecture (How it works)

1. The React frontend connects to the WebSocket endpoint (ws://localhost:8000/ws/search/).
2. User sends a JSON search message: `{ "action": "search", "term": "dune" }`.
3. Django Channels consumer receives the message and queries the database for active `SiteSource` records.
4. For each active site, the consumer dispatches a Celery task to the appropriate queue:
   - Sites that do not require a full browser -> `fast_queue`.
   - Sites that require Selenium/Playwright -> `profile_queue`.
5. Two separate Celery workers process jobs concurrently:
   - Fast worker: listens on `fast_queue` (e.g., concurrency 10).
   - Profile worker: listens on `profile_queue` (concurrency 1).
6. Each scraping task sends results back to the user's WebSocket channel as they complete.
7. The frontend receives streamed results and renders them in real time.

## Project structure

```
.
├── backend/
│   ├─ manage.py
│   ├─ requirements.txt
│   ├─ scraper_project/
│   │  ├─ settings.py
│   │  ├─ asgi.py
│   │  ├─ celery.py
│   │  ├─ urls.py
│   │  └─ __init__.py
│   ├─ scraper_api/
│   │  ├─ models.py         # SiteSource model
│   │  ├─ consumers.py      # AsyncJsonWebsocketConsumer (ws/search)
│   │  ├─ routing.py        # websocket_urlpatterns
+│   │  └─ tasks.py          # Celery tasks (scrape_site, etc.)
│   └─ train_profile.py      # Brave + selenium-stealth profile warmer
│
└── frontend/
    ├─ public/
    ├─ src/
    │  └─ App.jsx           # Main React component
    ├─ package.json
    ├─ tailwind.config.js  # Tailwind config
    └─ vite.config.js      # Vite config
```

## Setup & Installation

Prerequisites:

- Python 3.10+
- Node.js v16+
- Docker Desktop (recommended for Redis)

### 1) Start Redis (recommended)

Run this in a terminal (PowerShell):

```powershell
docker run -d -p 6379:6379 redis
```

Or start Redis from Docker Desktop UI.

### 2) Backend setup

Open a terminal and change into the `backend/` folder.

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install selenium-stealth
python manage.py migrate
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 3) Frontend setup

Open a separate terminal and change into the `frontend/` folder.

If you haven't already created the Vite project here, you can initialize with:

```powershell
npm create vite@latest . -- --template react
npm install
```

Install Tailwind and init config:

```powershell
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Edit `tailwind.config.js` to include your files:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
}
```

Replace `src/index.css` with the Tailwind directives:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 4) CRITICAL: Warm up your scraper profile (one-time step)

Your Selenium scrapers will likely fail until you warm up a persistent Brave profile. This creates a more "human" profile and helps bypass Cloudflare.

1. Close ALL Brave browser windows.
2. In your backend virtualenv terminal run:

```powershell
python train_profile.py
```

3. A Brave window will open for the bot profile. In that window:
   - Go to google.com and sign into a Google account (this helps make the profile appear human).
   - Visit any sites you plan to scrape that require a full browser and manually solve CAPTCHAs.
4. Once sites are trained, close the Brave window and stop the script with CTRL+C.

This warmed profile will be reused by Selenium scrapers.

## How to run the full application (4 terminals)

You should have four terminals open simultaneously. Use PowerShell on Windows as shown below.

Terminal 1 — Fast Lane Celery worker (for simple HTTP scrapers):

```powershell
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker -Q fast_queue -c 10 --pool=threads --loglevel=info
```

Terminal 2 — Profile Lane Celery worker (for Selenium scrapers):

```powershell
cd backend
.\venv\Scripts\activate
celery -A scraper_project worker -Q profile_queue -c 1 --pool=threads --loglevel=info
```

Terminal 3 — Daphne ASGI server:

```powershell
cd backend
.\venv\Scripts\activate
daphne -p 8000 scraper_project.asgi:application
```

Terminal 4 — Frontend dev server:

```powershell
cd frontend
npm run dev
```

Frontend will usually be at http://localhost:5173 and backend API/WS at http://localhost:8000

## Django Admin

Visit http://localhost:8000/admin/ and log in with the superuser you created.

Model: `SiteSource`

Each `SiteSource` should include:
- Base URL
- is_active
- Search method (GET/POST) and endpoint pattern with `%QUERY%`
- Requires full browser (boolean)
- CSS selectors for result container, title, link, poster, and attribute for images

## WebSocket API

WebSocket endpoint:

```
ws://localhost:8000/ws/search/
```

To start a search (client -> server):

```json
{ "action": "search", "term": "your movie" }
```

Server -> Client (example successful result):

```json
{
  "source": "HDHub4u1",
  "title": "Dune: Part Two (2024) - ...",
  "link": "https://...",
  "poster": "https://..."
}
```

Server -> Client (error):

```json
{
  "error": true,
  "message": "Failed to fetch data from Vegamovies"
}
```

## Notes & Troubleshooting

- If Selenium scrapers fail immediately, ensure the warmed Brave profile exists and Brave was closed when running `train_profile.py`.
- Use `-c 1` for the profile_queue worker to avoid multiple processes accessing the same profile simultaneously.
- Monitor Celery logs for per-task errors and the Daphne console for consumer-related exceptions.
- For development you can point to local/test sites and gradually add production targets once scrapers are stable.

## Next steps / improvements

- Add unit tests for consumers and scraping logic.
- Add Docker Compose for local dev (Redis, backend, workers, frontend) to simplify running the full stack.
- Add rate-limiting and per-site throttling to avoid bans.

## License

This project does not include a license file. Add one if you want to define reuse terms.

---

If you want, I can also:
- add a `CONTRIBUTING.md` or `docker-compose.yml` to run everything locally, or
- scaffold basic unit tests for the scraping tasks and consumer.
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
