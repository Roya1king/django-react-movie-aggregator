# Personal Movie Scraper Aggregator

This is a full-stack, real-time movie scraper and aggregator. It uses a React frontend, a Django (Channels) backend, and a robust Celery task queue to search multiple websites at once and stream the results back to the user over WebSockets.

The system is designed to be resilient, using two separate "lanes" (Celery queues) to process scrapers concurrently: one high-speed lane for simple sites and one "profile-locked" lane for sites that require a full browser to bypass bot detection.

## Core Features

- Real-Time Results: Uses WebSockets (django-channels) to stream results to the frontend as soon as they are found.
- Dynamic Admin Panel: Uses the built-in Django Admin to add, edit, or remove target websites, including their specific search patterns (CSS selectors).
- Multi-Site Scraping: Scrapes multiple sites in parallel.
- Robust Concurrency: Uses two separate Celery queues:
	- fast_queue: For simple requests (GET/POST) scrapers. Runs with high concurrency.
	- profile_queue: For complex selenium (Brave) scrapers. Runs with concurrency 1 to prevent profile-locking crashes.
- Cloudflare Bypass: Uses selenium-stealth and a "warmed-up" persistent Brave browser profile to bypass Cloudflare bot detection.

## Tech Stack

- Backend: Django, Django Channels, Celery, Redis
- Frontend: React
- Scraping: BeautifulSoup, Selenium, WebDriver-Manager, Selenium-Stealth (and optionally Playwright)
- Server: Daphne (ASGI server for Channels)

## Architecture (How it Works)

1. React Frontend connects to the WebSocket endpoint.
2. User sends a JSON search message (e.g., {"action": "search", "term": "dune"}).
3. Django (Channels Consumer) receives the message.
4. The Consumer queries the database for all "active" SiteSources.
5. It loops through them and dispatches Celery tasks to the correct queue:
	 - If Requires playwright/selenium is OFF: Send to fast_queue.
	 - If Requires playwright/selenium is ON: Send to profile_queue.
6. Two separate Celery workers are listening:
	 - Fast Worker processes all fast_queue jobs (up to 10 at a time).
	 - Profile Worker processes all profile_queue jobs (one at a time).
7. As each task finishes, it sends its results directly to the user's WebSocket channel.
8. React receives the result and adds it to the list.

## Project Structure

```
backend/
├─ manage.py
├─ requirements.txt
├─ scraper_project/
│  ├─ settings.py
│  ├─ asgi.py
│  ├─ celery.py
│  ├─ urls.py
│  └─ __init__.py
├─ scraper_api/
│  ├─ models.py            # SiteSource model
│  ├─ consumers.py         # AsyncJsonWebsocketConsumer (ws/search)
│  ├─ routing.py           # websocket_urlpatterns
│  └─ tasks.py             # Celery tasks (scrape_site, etc.)
└─ train_profile.py        # Brave + selenium-stealth profile warmer
```

## Endpoints

### 1) WebSocket

- URL: ws://localhost:8000/ws/search/
- Client > Server Message (To start a search):

```json
{
	"action": "search",
	"term": "your movie"
}
```

- Server > Client Message (A successful result):

```json
{
	"source": "HDHub4u1",
	"title": "Dune: Part Two (2024)...",
	"link": "https://...",
	"poster": "https://..."
}
```

- Server > Client Message (An error):

```json
{
	"error": true,
	"message": "Failed to fetch data from Vegamovies"
}
```

### 2) Django Admin

- URL: http://localhost:8000/admin/
- Login: Use the superuser you create during setup.
- Model: Go to "Site Sources" to add/edit your sites.

## Setup & Installation

### Prerequisites

- Python: A clean, official version (e.g., 3.10+). Do NOT use Anaconda.
- Node.js: (v16+) For the React frontend.
- Docker Desktop: The easiest way to run your Redis server.

### Step 1: Start Your Redis Server

Run this in a terminal. This will be Terminal 1.

```powershell
docker run -d -p 6379:6379 redis
```

(You can also use your Docker Desktop UI to start the Redis container).

### Step 2: Backend Setup

Navigate to your backend folder.

Create a new, clean virtual environment with your official Python:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\activate
```

Install all dependencies:

```powershell
pip install -r requirements.txt
pip install selenium-stealth
```

Initialize your database (this creates db.sqlite3):

```powershell
python manage.py migrate
```

Create your admin user:

```powershell
python manage.py createsuperuser
```

(Follow the prompts to set your username and password).

### Step 3: Frontend Setup

In a separate terminal, navigate to your frontend folder.

Install dependencies:

```powershell
npm install
```

## CRITICAL: How to "Warm Up" Your Scraper Profile

Your Selenium scrapers will fail until you do this one-time setup. This "warms up" your bot's browser profile to make it look human and bypass Cloudflare.

1. CLOSE ALL BRAVE BROWSER WINDOWS. (This is essential, or the script will crash).
2. In your backend terminal (with venv active), run the train_profile.py script:

```powershell
python train_profile.py
```

3. A new Brave window will pop up. This is your "bot" profile.
4. In this new window:
	 - Go to google.com and LOG IN to your Google account. This is the most important step.
	 - Visit https://hdhub4u.pictures/. Manually solve the CAPTCHA until you see the real site.
	 - Visit https://vegamovies.gripe/. Manually solve its CAPTCHA.
	 - Visit https://vegamovies.talk/. Manually solve its CAPTCHA.
	 - Do this for any site you've marked as requiring a full browser.
5. Once all sites are "trained," close the Brave window and stop the script (CTRL + C in the terminal).

Your profile is now "warmed up" and will be used by all your scrapers.

## How to Run the Full Application

You must have 4 terminals open and running at the same time.

### Terminal 1: The "Fast Lane" Worker (for requests)

Where: backend folder

```powershell
.\venv\Scripts\activate
celery -A scraper_project worker -Q fast_queue -c 10 --pool=threads --loglevel=info
```

### Terminal 2: The "Profile Lane" Worker (for selenium)

Where: backend folder

```powershell
.\venv\Scripts\activate
celery -A scraper_project worker -Q profile_queue -c 1 --pool=threads --loglevel=info
```

> Note: The `-c 1` (concurrency 1) is the magic fix that prevents your profile from crashing.

### Terminal 3: The Web Server (Daphne)

Where: backend folder

```powershell
.\venv\Scripts\activate
daphne -p 8000 scraper_project.asgi:application
```

### Terminal 4: The React App

Where: frontend folder

```powershell
npm start
```

You can now go to http://localhost:3000 (your React app) and start searching!

## Notes and Tips

- If you encounter `ModuleNotFoundError` for `daphne` or `rest_framework`, ensure your virtual environment is activated in each terminal, or start Daphne as `python -m daphne ...` to force venv usage.
- For Redis issues, confirm the container is running and listening on port 6379.
- For Cloudflare-protected sites, ensure you warmed up the Brave profile with `train_profile.py`.
- If you prefer Playwright for some sites, you can mark them accordingly in admin and run `python -m playwright install` once.

## WebSocket Contract (Reference)

- Connect to: `ws://127.0.0.1:8000/ws/search/`
- Request (from client): `{ "action": "search", "term": "oppenheimer" }`
- Streamed result (to client): `{ "source", "title", "link", "poster" }`
- Error: `{ "error": true, "message": "..." }`

## Admin: Configuring Site Sources

Define each target website in the Admin under Site Sources and fill in:
- Base URL, `is_active`
- Search method: GET/POST and endpoint with `%QUERY%`
- Whether the site requires a full browser (Selenium/Playwright)
- CSS selectors for result container, title, link, poster, and which attribute holds image URLs

---

For development only. Before production, review security settings, rotate SECRET_KEY, configure ALLOWED_HOSTS properly, and consider containerizing the stack.
