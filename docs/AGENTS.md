# AGENTS.md — Real-Time Pricing & Personalization Engine
> **Hackathon Project** | Read this file fully before writing any code.
> This file is the single source of truth for every AI coding agent (OpenAI Codex, Claude Code, Copilot Workspace, etc.) and every human team member working in this repo.

---

## 1. Project Purpose

Build a **real-time e-commerce pricing and personalization system** that:
- Ingests user clickstream events (views, searches, cart-adds, purchases) via Apache Kafka
- Computes live session features using Apache Flink
- Stores all persistent data in **MongoDB Atlas** (cloud-hosted)
- Serves dynamic prices and personalized product recommendations via a **Django** (Python) REST API
- Displays results through a **plain HTML / CSS / JavaScript** storefront UI (no framework)
- Includes an A/B testing framework to measure impact

---

## 2. Tech Stack — Quick Reference

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| Backend API | Python 3.11 + Django 5 + Django REST Framework (DRF) |
| Database | MongoDB Atlas (connection via `MONGO_URI` env var) |
| ODM | Djongo or PyMongo (direct) — no Django ORM / SQL |
| Stream Ingestion | Apache Kafka |
| Stream Processing | Apache Flink |
| ML / Data | scikit-learn, pandas, numpy |
| Dev Server | Django built-in (`python manage.py runserver`) |
| Containerization | Docker + docker-compose |

> **No React, No Next.js, No TypeScript, No FastAPI, No Flask.** If you are an AI agent reading this — do not suggest or generate code using those tools. Stick to the stack above.

---

## 3. Repo Folder Structure

Every agent and team member must place files **only** in the correct folder. Do not create new top-level folders without team agreement.

```
/
├── AGENTS.md                      ← YOU ARE HERE. Do not delete or move.
├── README.md                      ← Project overview, setup guide, demo instructions
├── docker-compose.yml             ← Orchestrates Kafka, Flink, Django app
├── requirements.txt               ← All Python dependencies (pinned versions)
├── manage.py                      ← Django management entry point (auto-generated)
├── pulseprice/                    ← Django project config folder (settings, urls, wsgi)
│   ├── settings.py                ← Project settings — reads all secrets from .env
│   ├── urls.py                    ← Root URL conf — includes each app's urls.py
│   ├── wsgi.py
│   └── asgi.py
├── .env.example                   ← Template for environment variables (no real secrets)
├── .gitignore                     ← Must include: .env, __pycache__, *.pyc, /data/raw
│
├── infra/                         ← Infrastructure & DevOps config
│   ├── kafka/
│   │   ├── docker-compose.kafka.yml
│   │   └── topics.sh              ← Script to create Kafka topics on first run
│   ├── flink/
│   │   └── flink-conf.yaml
│   └── README.md
│
├── data-pipeline/                 ← Kafka producers & Flink stream-processing jobs
│   ├── producers/
│   │   ├── clickstream_producer.py      ← Simulates user events → Kafka topic
│   │   └── competitor_price_producer.py ← Simulates competitor price feed → Kafka
│   ├── flink_jobs/
│   │   ├── session_features_job.py      ← Sessionization, engagement score, affinities
│   │   └── demand_velocity_job.py       ← Per-product real-time demand rate
│   ├── schemas/
│   │   └── events.py                    ← Dataclass schemas for all Kafka event types
│   └── README.md
│
├── database/                      ← MongoDB connection, collections, helpers
│   ├── connection.py              ← Creates and exports the MongoClient using MONGO_URI
│   ├── collections.py             ← Defines collection names as constants (never hardcode)
│   ├── seed.py                    ← Seeds product catalog and user segments on first run
│   └── README.md
│
├── pricing/                       ← Dynamic pricing model & business logic
│   ├── model/
│   │   ├── train.py               ← Trains pricing model (sklearn regression / bandit)
│   │   ├── predict.py             ← Loads saved model and runs inference
│   │   └── artifacts/             ← Saved .pkl model files — git-ignored
│   ├── rules.py                   ← Business guardrails (price floor, discount cap)
│   ├── pricing_engine.py          ← Orchestrates: fetch features → model → rules → price
│   └── README.md
│
├── recommendations/               ← Recommendation engine
│   ├── model/
│   │   ├── collaborative_filtering.py   ← Nearest-neighbors or ALS baseline
│   │   ├── session_model.py             ← Sequence-based model (GRU or simple RNN)
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── artifacts/             ← Saved model files — git-ignored
│   ├── cold_start.py              ← Fallback recs for new users (context-based)
│   ├── rec_engine.py              ← Hybrid: merges CF + session model scores
│   └── README.md
│
├── apps/                          ← Django applications (one app per domain)
│   │
│   ├── pricing_api/               ← Django app: dynamic pricing endpoints
│   │   ├── views.py               ← GET /api/price?product_id=&user_id=
│   │   ├── urls.py                ← URL patterns for this app
│   │   ├── serializers.py         ← DRF serializers for request/response validation
│   │   ├── services.py            ← Calls pricing_engine, returns serializer-safe dict
│   │   └── apps.py
│   │
│   ├── recommendations_api/       ← Django app: recommendation endpoints
│   │   ├── views.py               ← GET /api/recommendations?user_id=
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py            ← Calls rec_engine, returns serializer-safe dict
│   │   └── apps.py
│   │
│   ├── events_api/                ← Django app: ingest user click/view events
│   │   ├── views.py               ← POST /api/events
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   └── apps.py
│   │
│   └── health/                    ← Django app: health check
│       ├── views.py               ← GET /api/health
│       ├── urls.py
│       └── apps.py
│
├── middleware/                    ← Custom Django middleware
│   └── ab_testing.py              ← Assigns experiment variant on every API request
│
├── ab-testing/                    ← A/B experiment tracking & analysis
│   ├── assignment.py              ← SHA-256 hash-based variant assignment
│   ├── logger.py                  ← Writes experiment events to MongoDB
│   ├── metrics.py                 ← Computes CR, AOV, revenue-per-session from DB
│   ├── analysis.ipynb             ← Statistical significance notebook
│   └── README.md
│
├── ml-notebooks/                  ← EDA & model experimentation (not production code)
│   ├── 01_eda_clickstream.ipynb
│   ├── 02_pricing_model_dev.ipynb
│   ├── 03_rec_model_dev.ipynb
│   └── 04_fairness_audit.ipynb
│
├── data/                          ← Synthetic datasets for local dev & seeding
│   ├── product_catalog.json       ← 5000+ SKUs with base_price, cost, category
│   ├── competitor_prices.json
│   └── user_segments.json
│
├── frontend/                      ← Plain HTML / CSS / JS storefront UI
│   ├── index.html                 ← Main storefront page
│   ├── product.html               ← Single product detail page
│   ├── css/
│   │   ├── main.css               ← Global styles, CSS variables, reset
│   │   ├── components.css         ← Product card, badge, navbar styles
│   │   └── layout.css             ← Grid/flex layout helpers
│   ├── js/
│   │   ├── api.js                 ← All fetch() calls to Django API (single source of truth)
│   │   ├── store.js               ← Simple in-memory state (current user, session ID)
│   │   ├── productCard.js         ← Renders a product card DOM element dynamically
│   │   ├── recommendations.js     ← Fetches and renders recommendation rows
│   │   ├── pricing.js             ← Fetches dynamic price and updates DOM
│   │   └── main.js                ← Entry point: initialises page on DOMContentLoaded
│   └── README.md
│
└── tests/                         ← All tests — mirrors source structure
    ├── unit/
    │   ├── test_pricing_rules.py
    │   ├── test_rec_engine.py
    │   └── test_ab_assignment.py
    ├── integration/
    │   ├── test_api_pricing.py    ← Uses Django test client
    │   └── test_api_recommendations.py
    └── README.md
```

---

## 4. Team Roles & Module Ownership

Each team member owns one or more modules. **Only modify files inside your owned folders unless you coordinate with the owner first.**

| Name | Role | Owned Folders | Primary Responsibility |
|---|---|---|---|
| [Your Name] | [Your Role Title] | [e.g. `api/`, `database/`] | [One-line description] |
| [Your Name] | [Your Role Title] | [e.g. `data-pipeline/`, `infra/`] | [One-line description] |
| [Your Name] | [Your Role Title] | [e.g. `pricing/`, `ml-notebooks/`] | [One-line description] |
| [Your Name] | [Your Role Title] | [e.g. `recommendations/`] | [One-line description] |
| [Your Name] | [Your Role Title] | [e.g. `frontend/`, `ab-testing/`] | [One-line description] |

> **Instructions for every team member:**
> 1. Replace a placeholder row above with your actual name, role title, folder(s) you own, and a one-line description.
> 2. Keep the Markdown table pipes intact — do not break formatting.
> 3. Make updating this table your very first commit to the repo.

---

## 5. Coding Standards (All Agents & Members Must Follow)

### Python (Backend — Django)
- **Python 3.11+** only
- Format with **Black** (`black .`) before every commit
- Lint with **Ruff** (`ruff check .`)
- Type-hint every function signature
- Use **`django-environ`** or **`python-dotenv`** to load `.env` into `settings.py` — never hardcode secrets
- One Django **app per domain** (pricing, recommendations, events, health) — do not dump all views into one app
- All views must be **class-based DRF APIViews** (`from rest_framework.views import APIView`) — no function-based views except for health check
- All request/response shapes are defined in **DRF Serializers** in each app's `serializers.py` — never validate manually in views
- All business logic lives in `services.py` — views only call the service and return the response
- **Do not use Django ORM or `django.db`** — we use MongoDB via PyMongo. Set `DATABASES = {}` in settings to disable SQL entirely

### JavaScript (Frontend)
- **Vanilla ES6+** only — no jQuery, no React, no Vue, no build step required
- Use `const` and `let` — never `var`
- All `fetch()` API calls must live in `frontend/js/api.js` only — never inline in HTML or other JS files
- Use `async/await` — no raw `.then()` chains
- DOM manipulation happens in the relevant JS module (e.g. `productCard.js`), not in `main.js`
- No inline `<script>` tags in HTML files — always link external JS files with `defer`

### HTML / CSS
- Semantic HTML5 elements (`<main>`, `<section>`, `<article>`, `<nav>`, etc.)
- CSS variables defined in `:root` inside `main.css` — use them everywhere, no hardcoded hex colors
- Mobile-first responsive design using CSS Grid and Flexbox
- No inline `style=""` attributes anywhere

### Git Conventions
- Branch naming: `feat/<module>/<short-description>` — e.g. `feat/pricing/guardrail-rules`
- Commit messages: `<type>(<scope>): <description>` — e.g. `feat(api): add /api/price route`
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- **Never commit directly to `main`.** Open a PR; at least one teammate must review.
- **Never commit `.env`** — it is git-ignored. Use `.env.example` only.

---

## 6. Environment Variables

All secrets and config live in `.env` (git-ignored). Copy `.env.example` to get started.

```
# .env.example — copy this to .env and fill in real values

# MongoDB
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority
MONGO_DB_NAME=ecommerce_pricing

# Django
DJANGO_SECRET_KEY=replace-with-a-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_PORT=8000

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CLICKSTREAM_TOPIC=user-events
KAFKA_COMPETITOR_TOPIC=competitor-prices
```

> **MONGO_URI already exists for this project.** Paste the real connection string into your local `.env` file only. Never paste it into any Python/JS file or commit it.

---

## 7. MongoDB Collections Reference

All collection names are defined as constants in `database/collections.py`. Always import from there — never hardcode a collection name as a string in routes or services.

| Constant | Collection Name | Stores |
|---|---|---|
| `PRODUCTS` | `products` | Product catalog (SKU, name, base_price, cost, category) |
| `USERS` | `users` | User profiles and segment labels |
| `EVENTS` | `clickstream_events` | Every user event (view, search, cart, purchase) |
| `SESSIONS` | `sessions` | Live session features computed by Flink |
| `PRICES` | `dynamic_prices` | Price history per product/user pair |
| `RECOMMENDATIONS` | `recommendations` | Cached recommendation lists per user |
| `AB_LOGS` | `ab_experiment_logs` | Experiment impressions and outcomes |

---

## 8. Agent-Specific Instructions

> These rules tell AI coding agents (Codex, Claude Code, etc.) exactly how to behave in this repo.

### General Rules
- **Always read the `README.md`** inside a module folder before editing any file in it.
- **Use only the approved tech stack** (Django + DRF, PyMongo, Vanilla JS). Do not introduce FastAPI, Flask, React, SQLAlchemy, or any unapproved dependency.
- **Never generate placeholder logic** in production files. Write real, working code.
- If a function depends on a missing model artifact, raise `NotImplementedError` with a clear message.
- **Tests are mandatory.** Every new Django view or engine function must have a test in `tests/`.
- Keep every file under **250 lines**. Split into submodules if larger.

### When Working on `database/`
- All MongoDB interactions use the client from `database/connection.py` — never instantiate a new `MongoClient` elsewhere.
- Use collection name constants from `database/collections.py` — e.g. `db[PRODUCTS]`, never `db["products"]`.
- Always handle `pymongo.errors.ConnectionFailure` and `pymongo.errors.OperationFailure` with proper error logging.

### When Working on `apps/` (Django API)
- Every view must be a **DRF APIView** subclass. Return `Response(data, status=status.HTTP_200_OK)` — never `JsonResponse` or `HttpResponse` for API routes.
- Input validation always goes through a **DRF Serializer** in the app's `serializers.py` — never read `request.data["key"]` directly in a view.
- Business logic always lives in the app's `services.py` — views must stay thin (validate → call service → return response).
- Register each app's `urls.py` in `pulseprice/urls.py` using `path("api/", include("apps.<app_name>.urls"))`.
- Enable CORS via `django-cors-headers` configured in `settings.py` so the HTML frontend can call the API.
- The A/B middleware in `middleware/ab_testing.py` must be listed in `MIDDLEWARE` in `settings.py` and tag every request to `/api/price` and `/api/recommendations` with `experiment_variant`.
- Target response time: **< 200ms** for all `/api/` endpoints.
- **Disable Django SQL ORM completely**: set `DATABASES = {}` in `settings.py`. All data goes through `database/connection.py` (PyMongo).

### When Working on `pricing/`
- The `rules.py` guardrail layer must **always** be called after model inference — never return a raw model price to the API.
- Guardrail defaults: `min_price = cost * 1.10`, `max_discount = 0.30` (30% off base).
- The pricing model must accept these feature keys: `demand_velocity`, `inventory_ratio`, `competitor_price`, `user_wtp_score`, `hour_of_day`.
- Every price response must include a `reason` field (string) explaining the price to the user.

### When Working on `recommendations/`
- `cold_start.py` must not use: `gender`, `age`, `ethnicity`, `location` — behavioral signals only.
- `rec_engine.py` must always blend both CF and session model scores before returning results.
- Always return exactly `top_n` items (default: 10). If the model returns fewer, pad with popular items.

### When Working on `frontend/`
- All API calls go in `js/api.js` only. Use `const BASE_URL = 'http://localhost:8000'` at the top of that file.
- Every product card must display a price explanation badge with one of: `"High demand"`, `"Limited stock"`, `"Personalized offer"`, `"Flash sale"`.
- No inline `style=""`. No `var`. No jQuery. No external UI libraries.
- Show a loading skeleton while API calls are in-flight — never leave the UI blank.
- Handle API errors gracefully — display a user-friendly error message in the DOM, never `console.error` only.

### When Working on `data-pipeline/`
- Kafka topic names come from `.env` via `os.getenv('KAFKA_CLICKSTREAM_TOPIC')` — never hardcode.
- Flink jobs must use event-time semantics with watermarks.
- After computing session features, write them to MongoDB `sessions` collection using the `database/connection.py` client.

### When Working on `ab-testing/`
- Variant assignment must be deterministic: SHA-256 of `user_id + experiment_id`, then `% 2` for A/B split.
- Every experiment event logged to MongoDB must follow this exact schema:
  ```json
  {
    "experiment_id": "string",
    "user_id": "string",
    "variant": "A" | "B",
    "event_type": "impression" | "click" | "purchase",
    "product_id": "string or null",
    "revenue": "float or null",
    "timestamp": "ISO 8601 string"
  }
  ```

### When Working on `tests/`
- Use **pytest** + **pytest-django** for all tests.
- For Django view tests, use Django's `APIClient` from DRF (`from rest_framework.test import APIClient`) — do not spin up a real server.
- Mock all MongoDB calls with `unittest.mock.patch` — no real DB hits in unit tests.
- Minimum coverage target: **75%** for `apps/`, `pricing/`, and `recommendations/`.

---

## 9. Local Development Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd <repo-name>

# 2. Set up environment
cp .env.example .env
# Open .env and paste in the real MONGO_URI, DJANGO_SECRET_KEY, etc.

# 3. Create Python virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Start Kafka (needs Docker)
docker-compose up -d kafka

# 6. Seed the database (run once)
python database/seed.py

# 7. Start the Django API
python manage.py runserver 8000

# 8. Open the frontend
# Just open frontend/index.html in a browser, or use Live Server in VS Code.
# The JS files call http://localhost:8000 directly.

# 9. (Optional) Run Kafka producers to generate synthetic events
python data-pipeline/producers/clickstream_producer.py
```

---

## 10. Key Design Decisions (Do Not Reverse Without Discussion)

| Decision | Rationale |
|---|---|
| Django + DRF over Flask | Built-in structure (apps, settings, middleware), DRF gives serializers + APIView out of the box — less boilerplate for a team working in parallel |
| MongoDB Atlas over SQL | Schema-flexible for evolving event/session data; free tier available |
| PyMongo (direct) over Djongo/MongoEngine | Most reliable MongoDB driver; Djongo has known compatibility issues with Django 5 |
| Django ORM disabled (`DATABASES = {}`) | We don't use SQL — disabling prevents accidental ORM usage by teammates |
| Vanilla JS over React | No build step, no node_modules, instant browser reload during dev |
| All fetch() calls in `api.js` | Single file to update if base URL or auth headers change |
| SHA-256 for A/B assignment | Deterministic without a DB lookup; same user always gets same variant |
| Guardrails always after ML | Business rules are non-negotiable; ML optimizes within the safe range |

---

## 11. Fairness & Ethics Requirements

These are **hard requirements**, not suggestions:

1. **No protected attributes** — pricing and rec models must never use race, gender, religion, age, or nationality — not even as proxies.
2. **Price floor enforced in `rules.py`** — no product can be priced below `cost * 1.10`.
3. **Reason string required** — every `/api/price` response must include a `reason` field shown to the user in the UI.
4. **Fairness audit** — `ml-notebooks/04_fairness_audit.ipynb` must be run and committed before demo day.

---

## 12. Definition of Done

A feature is **done** when all boxes are checked:

- [ ] Code is in the correct module folder per the structure in Section 3
- [ ] All Python functions have type hints and a docstring
- [ ] No linting errors (`ruff check . && black --check .`)
- [ ] Tests written and passing (`pytest --ds=pulseprice.settings tests/`)
- [ ] PR opened with a clear description; at least one teammate has reviewed and approved
- [ ] The module's `README.md` is updated if setup steps changed

---

*Last updated: April 2026 | Update the Team Roles table (Section 4) with your name and module before your first commit.*
# Grocery Admin Override

This addendum supersedes older generic e-commerce wording below whenever there is a conflict.

- The project should now be treated as a **grocery commerce** platform.
- The first major product surface is the **grocery admin dashboard**.
- Admin work should prioritize dashboard, catalog, inventory, and order operations.
- Keep the approved stack unchanged: Django + DRF, PyMongo, vanilla HTML/CSS/JS.
- Keep all secrets in `.env` only and never commit real credentials.
