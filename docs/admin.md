# Admin Module Guide (PulsePrice Admin)

This document explains what the admin system is, what features it has, how data flows, and how to run it correctly.

## 1) What The Admin Is Used For

The admin panel is a **business-control dashboard** for grocery operations.  
It is designed for:

- pricing monitoring
- product and stock visibility
- recommendation quality checks
- user segment analysis
- pipeline and fairness monitoring

Main file:

- `frontend/admin.html`

Main admin API server:

- `api/server.py`

---

## 2) Admin Feature Set (Detailed)

### Overview section

- KPI cards:
  - total revenue today
  - active sessions
  - prices updated
  - average order value
- Revenue trend chart (Plotly line)
- Price adjustment reasons chart (Plotly donut)
- Recent price changes table

### Pricing Engine section

- Model status (type, last trained, accuracy)
- Guardrail rules (min price, max discount, compliance)
- Demand signals summary
- Top movers table
- Price distribution chart

### Recommendations section

- Recommendation CTR
- Avg recommendations per session
- Cold-start rate
- Model accuracy
- Session model table
- Category recommendations chart
- Cold-start signals tags

### A/B Experiments section

- Experiment list table
- Variant A vs B metrics comparison
- Confidence + winner hint
- Event log table

### Products section

- Product list table (sku, category, prices, cost, margin, stock, status)
- Category filter support

### Users & Segments section

- Total users / active today / new this week
- Segment cards with KPI bars
- User session table
- 3D scatter visualization (with fullscreen mode)

### Pipeline Monitor section

- Kafka status card
- Flink status card
- MongoDB status card
- Throughput chart
- Live event feed simulation

### Fairness Audit section

- Fairness checks cards
- Segment disparity chart
- Feature governance tags (used vs blocked features)

### Forecasting Lab section

- training UI flow
- source switch (kaggle/upload style interaction)
- progress simulation + prediction UI flow
- action buttons with toast feedback

---

## 3) Tech Stack Used By Admin

- Frontend: vanilla HTML/CSS/JS (`frontend/admin.html`)
- Charts: Plotly CDN
- Admin API: Flask (`api/server.py`)
- Data source:
  - MongoDB mode (if `.env` has valid Mongo URI)
  - Demo fallback mode (automatic if Mongo unavailable)

---

## 4) Admin API Endpoints Used

The dashboard calls these routes:

- `/api/health`
- `/api/kpi`
- `/api/revenue`
- `/api/price-changes`
- `/api/adjustment-reasons`
- `/api/pricing-engine`
- `/api/products`
- `/api/recommendations`
- `/api/user-segments`
- `/api/user-sessions`
- `/api/ab-experiments`
- `/api/ab-events`
- `/api/pipeline`
- `/api/throughput`
- `/api/fairness`
- `/api/user-counts`

---

## 5) How To Run Admin (Correct Way)

Use 2 terminals.

### Terminal 1: start admin API

```powershell
cd "E:\DA IICT V.01\DA-IICT"
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python api\server.py
```

Expected:

- Admin API on `http://127.0.0.1:5000`
- If Mongo is not configured, it runs in **demo mode** (still usable)

### Terminal 2: start frontend static server

```powershell
cd "E:\DA IICT V.01\DA-IICT"
python -m http.server 5510 --directory frontend
```

Open:

- `http://127.0.0.1:5510/admin.html`

---

## 6) Why Earlier It Was Not Working

Main issues that were fixed:

- `admin.html` had broken/incomplete JavaScript near fullscreen block, which stopped all click handlers and data rendering.
- `.env` had placeholder Mongo URI; API could crash before serving data.
- API now supports safe fallback demo mode.

---

## 7) User Side vs Admin Side (Important)

These are separate runtimes:

- **Admin side**:
  - `api/server.py` (Flask) + `frontend/admin.html`
- **User side**:
  - `mainProject/manage.py runserver 8001` (Django app)

They can run at the same time on different ports.

---

## 8) Common Troubleshooting

### Page opens but no data

- Check API is running on port `5000`.
- Open `http://127.0.0.1:5000/api/health`.

### Buttons not working

- Hard refresh browser (`Ctrl + F5`) to clear old JS cache.

### `ERR_CONNECTION_REFUSED`

- The server for that port is not running.
- Start the related command again.

### Django user side won’t start

- Use project venv:
  - `.\venv\Scripts\Activate.ps1`
- Run:
  - `python mainProject\manage.py runserver 8001`

---

## 9) Team Handover Quick Notes

If teammate wants admin quickly:

1. Clone repo
2. Install `requirements.txt`
3. Start `python api/server.py`
4. Start frontend server on `5510`
5. Open `admin.html`

If teammate wants user app:

1. Install `mainProject/requirements.txt`
2. Run `python mainProject/manage.py runserver 8001`
3. Open `/login/` or `/`

---

## 10) Full Kafka Connection (Real, Not Simulated)

The repo is now wired for real Kafka metrics in admin API.

### What was connected

- Kafka Docker setup:
  - `docker-compose.yml`
  - `infra/kafka/docker-compose.kafka.yml`
- Topic script:
  - `infra/kafka/topics.sh`
- Producers:
  - `data-pipeline/producers/clickstream_producer.py`
  - `data-pipeline/producers/competitor_price_producer.py`
- Admin API Kafka monitor endpoint:
  - `api/server.py`
  - new route: `/api/kafka/stream`

### Start full Kafka pipeline

1. Start Kafka + Kafka UI:

```powershell
cd "E:\DA IICT V.01\DA-IICT"
docker compose up -d kafka kafka-ui
```

2. Start clickstream producer:

```powershell
cd "E:\DA IICT V.01\DA-IICT"
.\venv\Scripts\Activate.ps1
python data-pipeline\producers\clickstream_producer.py --rate 8
```

3. Start competitor producer (new terminal):

```powershell
cd "E:\DA IICT V.01\DA-IICT"
.\venv\Scripts\Activate.ps1
python data-pipeline\producers\competitor_price_producer.py --rate 2
```

4. Start admin API:

```powershell
cd "E:\DA IICT V.01\DA-IICT"
.\venv\Scripts\Activate.ps1
python api\server.py
```

5. Verify Kafka connection:

- `http://127.0.0.1:5000/api/health`
- `http://127.0.0.1:5000/api/kafka/stream`

When connected, you should see:

- `"kafka_connected": true`
- `messages_sec > 0` after producers run

### Kafka UI

- Open `http://127.0.0.1:8080`
- You can inspect topics and message flow.
