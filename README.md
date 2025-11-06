
---

```markdown
# 🎬 Django + React Real-Time Scraper Engine

A **full-stack real-time movie scraper and aggregator**, designed as a personal dashboard that can query multiple sites **simultaneously** — even **Cloudflare-protected** ones — and stream the results back to a web interface **in real-time**.

---

## 🧠 Core Architecture

- **Backend:** Django + Django Channels (WebSockets)  
- **Frontend:** React (built with **Vite**, served directly by Django)  
- **Task Queuing:** Celery + Redis  
- **Scraping Engine:**
  - `requests` + `BeautifulSoup` → for fast and simple sites  
  - `Selenium` + **Brave Browser** → for Cloudflare-protected or JavaScript-heavy sites  
- **Concurrency Model:**  
  - `fast_queue` → for lightweight request-based scrapers  
  - `profile_queue` → for heavy Selenium tasks (run one at a time to prevent Brave profile corruption)

---

## 📁 Project Structure

```

my_search_project/
├── backend/
│   ├── manage.py
│   ├── train_profile.py        <-- IMPORTANT: warms up Brave profile
│   ├── requirements.txt
│   ├── scraper_project/        (Django project)
│   └── scraper_api/            (Django app)
├── frontend/
│   ├── dist/                   <-- React app build output
│   ├── src/
│   ├── package.json
│   └── vite.config.js          <-- Configured for Django
└── README.md                   <-- This file

````

---

## ⚙️ Prerequisites

1. **Python 3.10+** (✅ You are using 3.14 — perfect)  
2. **Node.js & npm** — for building the React app  
3. **Docker Desktop** — to run Redis easily  
4. **Brave Browser** — must be installed in the default location  

---

## 🚀 Step 1: One-Time Project Setup

### 🟥 A. Start Redis (Docker)

Start Redis in a Docker container (only once):

```bash
docker run -d -p 6379:6379 --name my-scraper-redis redis
````

> 💡 If you get “port already allocated”, it just means Redis is already running (visible in Docker Desktop).

---

### 🟩 B. Backend Setup

Open a terminal in the `backend/` folder.

#### 1. Create and activate a virtual environment

```bash
python -m venv venv
.\venv\Scripts\activate
```

#### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install selenium-stealth webdriver-manager
```

#### 3. Initialize the database

```bash
python manage.py migrate
```

#### 4. Create an admin user

```bash
python manage.py createsuperuser
```

---

### 🟦 C. Frontend Setup

Open a **new terminal** in the `frontend/` folder.

#### 1. Install Node modules

```bash
npm install
```

#### 2. Build the React app

```bash
npm run build
```

> 🏗️ This creates the `frontend/dist/` folder, which Django will serve.

---

### 🔥 D. Browser Profile Warm-Up (**CRITICAL**)

This step “trains” your Selenium Brave profile to look like a real human user and defeat Cloudflare.

#### 1. Close **all** Brave browser windows.

#### 2. Run the training script:

```bash
# In backend/ (with venv active)
python train_profile.py
```

A **Brave window** will pop up — this is your **BraveSeleniumProfile**.

#### 3. In that Brave window:

1. Go to [https://google.com](https://google.com) → log in with your Google account (this builds trust).
2. Visit and manually solve CAPTCHAs on:

   * [https://hdhub4u.pictures/](https://hdhub4u.pictures/)
   * [https://vegamovies.gripe/](https://vegamovies.gripe/)
   * [https://vegamovies.talk/](https://vegamovies.talk/)
3. Once all sites load normally → **close Brave** and stop the script (`CTRL + C`).

✅ Your profile is now warmed and trusted.

---

## 🏃 Step 2: Run the Project

You need **three backend terminals** (plus Docker running Redis).
You do **not** need to run `npm start`.

---

### 🧩 Terminal 1: Fast Queue Worker

Handles lightweight `requests`-based scrapers.

```bash
# In backend/
.\venv\Scripts\activate
celery -A scraper_project worker --pool=threads -Q fast_queue -c 12 --loglevel=info
```

---

### 🧩 Terminal 2: Selenium/Profile Queue Worker

Handles Selenium scrapers one at a time (safe mode).

```bash
# In backend/
.\venv\Scripts\activate
celery -A scraper_project worker --pool=threads -Q profile_queue -c 1 --loglevel=info
```

---

### 🧩 Terminal 3: Web Server (Daphne)

Serves React frontend + WebSocket connections.

```bash
# In backend/
.\venv\Scripts\activate
daphne -p 8000 scraper_project.asgi:application
```

Your app is live 🎉

* **Frontend:** [http://localhost:8000](http://localhost:8000)
* **Admin Panel:** [http://localhost:8000/admin](http://localhost:8000/admin)

---

## ⚙️ Step 3: Configure Scrapers (via Admin)

1. Go to [http://localhost:8000/admin](http://localhost:8000/admin)
2. Log in with your superuser credentials.
3. Under **“Site Sources”**, click **“Add Site Source +”**.
4. Fill in each site’s scraping pattern.

---

### 🧩 Example: HDHub4u

| Field                         | Value                                                |
| ----------------------------- | ---------------------------------------------------- |
| **Name**                      | HDHub4u                                              |
| **Base URL**                  | [https://hdhub4u.pictures](https://hdhub4u.pictures) |
| **Search Type**               | GET Parameter                                        |
| **Search Endpoint**           | `/?s=%QUERY%`                                        |
| **Requires playwright**       | ✅ *(Sends to Selenium queue)*                        |
| **Result container selector** | `li.thumb`                                           |
| **Result title selector**     | `figcaption a p`                                     |
| **Result link selector**      | `figcaption a`                                       |
| **Result poster selector**    | `figure img`                                         |
| **Result poster attribute**   | `src`                                                |

---

### 🧩 Example: Vegamovies.talk

| Field                         | Value                                              |
| ----------------------------- | -------------------------------------------------- |
| **Name**                      | Vegamovies.talk                                    |
| **Base URL**                  | [https://vegamovies.talk](https://vegamovies.talk) |
| **Search Type**               | POST API                                           |
| **Search Endpoint**           | `/`                                                |
| **Post Payload Template**     | `do=search`, `subaction=search`, `story=%QUERY%`   |
| **Requires playwright**       | ✅                                                  |
| **Result container selector** | `article.post-item`                                |
| **Result title selector**     | `h3.entry-title a`                                 |
| **Result link selector**      | `h3.entry-title a`                                 |
| **Result poster selector**    | `img.blog-picture`                                 |
| **Result poster attribute**   | `src`                                              |

---

### 🧩 Example: Vegamovies.gripe

| Field                         | Value                                                |
| ----------------------------- | ---------------------------------------------------- |
| **Name**                      | Vegamovies                                           |
| **Base URL**                  | [https://vegamovies.gripe](https://vegamovies.gripe) |
| **Search Type**               | GET Parameter                                        |
| **Search Endpoint**           | `/?s=%QUERY%`                                        |
| **Requires playwright**       | ✅                                                    |
| **Result container selector** | `article.grid-item`                                  |
| **Result title selector**     | `h2.post-title a`                                    |
| **Result link selector**      | `h2.post-title a`                                    |
| **Result poster selector**    | `img.wp-post-image`                                  |
| **Result poster attribute**   | `src`                                                |

---

## 🔌 WebSocket API

**Endpoint:**

```
ws://localhost:8000/ws/search/
```

### 🔄 Client → Server (Start a Search)

```json
{
  "action": "search",
  "term": "your movie"
}
```

### 📡 Server → Client (Result)

```json
{
  "source": "SiteName",
  "title": "Movie Title",
  "link": "https://...",
  "poster": "https://..."
}
```

### ⚠️ Server → Client (Error)

```json
{
  "error": true,
  "message": "Failed to fetch data from ..."
}
```

---

## 🧭 Notes & Tips

* Always **train your Brave profile** before using Selenium scrapers.
* You can add or remove sources dynamically via the Admin Panel.
* The **frontend is static** — you only rebuild (`npm run build`) if you modify it.
* For production, configure your `.env` and run **Daphne + Celery workers** with a process manager like `supervisor` or `systemd`.

---

## 🏁 That’s It!

Your **Django + React Real-Time Scraper Engine** is ready.
You now have a **parallel, Cloudflare-resistant scraping system** that streams movie results instantly.
