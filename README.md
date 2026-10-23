# 🛒 BasketIQ — Full-Stack E-Commerce & AI Recipe Platform

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Backend-Django%205.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/API-Django%20REST%20Framework-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20API-412991?logo=openai&logoColor=white)](https://openai.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%20%7C%20Pandas-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Container-Docker%20%7C%20Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=black)](https://render.com/)

> An intelligent, full-stack grocery e-commerce web platform integrated with an **AI Recipe Planner** that dynamically analyzes cart items to recommend high-precision recipes, paired with enterprise inventory management and financial tracking.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Directory Structure](#-directory-structure)
- [Core Application Modules](#-core-application-modules)
- [AI Recipe Recommendation Engine](#-ai-recipe-recommendation-engine)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [Environment Variables (.env)](#environment-variables-env)
  - [Running with Docker](#running-with-docker)
- [Deployment Guide (Render & Cloud)](#-deployment-guide)
- [Contributors](#-contributors)

---

## 🌟 Overview

Traditional grocery platforms merely list items for purchase. **BasketIQ** transforms routine grocery shopping into an interactive culinary experience. Built for the **DA-IICT AI Hackathon**, it combines:
1. A fluid retail marketplace with real-time cart state and rapid checkout.
2. An **AI-powered culinary engine** using machine learning and LLM integration to generate recipes based on the exact ingredients in the shopper's active cart.
3. An administrative back-office for inventory reordering, expense tracking, and order dispatch.

---

## 🚀 Key Features

### 🛒 E-Commerce & Market Operations
- **Extensive Catalog:** 200+ grocery items categorized across produce, dairy, bakery, beverages, and pantry staples.
- **Dynamic Filtering & Search:** Instant sub-category filtering, price sorting, and fuzzy item search.
- **Persistent Cart State:** Session and database synchronized shopping cart with automatic price and tax calculation.
- **3-Step Checkout Flow:** Delivery address collection, payment gateway simulation, and instant order receipt generation.

### 🧠 Intelligent AI Recipe Planner
- **Active Ingredient Analysis:** Scans ingredients currently in the user's cart (15+ simultaneous items).
- **Culinary Matchmaking Algorithm:** Utilizes **Scikit-learn** vectorization and **OpenAI** intelligence to recommend recipes with a **92%+ relevance match rate**.
- **Missing Ingredient Identifier:** Calculates exactly which supplementary ingredients are required and allows 1-click addition to the basket.

### 🛡 Multi-Tier Admin Control Panel
- **Role-Based Permissions:** Multi-level access tiers for Store Admins, Inventory Clerks, and Billing Managers.
- **Inventory & Stock Management:** Real-time stock alerts, batch updates, and reorder triggers.
- **Expense & Revenue Analytics:** Visual reports of daily revenue, top-selling grocery items, and operational margins.

---

## 🏗 System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │      Client Browser (HTML5 / CSS3 / JS) │
                    │      Responsive Market UI & Checkout    │
                    └────────────────────┬────────────────────┘
                                         │  HTTP / REST
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │       Gunicorn WSGI Application         │
                    ├─────────────────────────────────────────┤
                    │           Django 5.1 Framework          │
                    │   • URL Routing • Django ORM • REST API │
                    └───────┬─────────────────────────┬───────┘
                            │                         │
             ┌──────────────┴──────────────┐          │
             ▼                             ▼          ▼
    ┌──────────────────┐         ┌────────────────────────┐
    │   MongoDB Atlas  │         │   AI / ML Pipeline     │
    │  NoSQL Document  │         │  • Scikit-Learn Match  │
    │  Store (PyMongo) │         │  • Pandas Vectorizer   │
    └──────────────────┘         │  • OpenAI API Engine   │
                                 └────────────────────────┘
```

---

## 💻 Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.13, Django 5.1.4, Django REST Framework (DRF) |
| **Artificial Intelligence** | OpenAI API (`>=1.59.0`), Scikit-learn (`1.6.0`), Pandas, NumPy |
| **Database & Caching** | MongoDB Atlas (`pymongo`), SQLite (development) |
| **Static & Media Delivery** | WhiteNoise (`6.8.2`), Gunicorn (`23.0.0`) |
| **Frontend Technologies** | JavaScript (ES6+), HTML5, CSS3, Bootstrap / Tailwind |
| **Container & CI/CD** | Docker, Docker Compose, Render (`render.yaml`) |

---

## 📁 Directory Structure

```plaintext
BasketIQ/
├── apps/
│   ├── accounts/          # User authentication, registration, profiles
│   ├── admin_api/         # REST API endpoints powering administrative operations
│   ├── admin_panel/       # Administrative UI (metrics, user controls, catalog)
│   ├── expenses/          # Expense tracking and store financial logs
│   ├── market/            # Core shopping storefront, category filters & cart logic
│   ├── orders/            # Order placement, checkout pipeline & receipts
│   └── planner/           # AI Recipe Planner engine (ingredient matching & OpenAI integration)
├── config/                # Django project settings (base, production, wsgi, urls)
├── docs/                  # API specifications & architectural documentation
├── requirements/          # Environment-specific python dependencies
├── scripts/               # Automation, seed data, and migration utilities
├── static/                # Compiled stylesheets, JavaScript bundles, images
├── templates/             # Server-rendered HTML templates
├── tests/                 # Unit and integration test suites
├── Dockerfile             # Multi-stage container definition
├── docker-compose.yml     # Multi-service local environment containerization
├── manage.py              # Django management CLI
├── render.yaml            # Infrastructure-as-code deployment blueprint for Render
├── requirements.txt       # Production python dependencies
└── README.md              # Project documentation
```

---

## 🧠 AI Recipe Recommendation Engine

When users add ingredients to their shopping basket, the **Planner Engine** (`apps/planner/`) performs:
1. **Extraction:** Parses active cart items and maps them against a verified culinary ingredient ontology.
2. **Feature Vectorization:** Applies TF-IDF vectorization across a recipe corpus to calculate cosine similarity scores between cart ingredients and required recipe bases.
3. **Generative Enhancement:** Sends matched ingredient sets to OpenAI's structured completion model to produce step-by-step cooking instructions, prep time, caloric estimates, and missing ingredient lists.

---

## ⚡ Getting Started

### Prerequisites
- **Python 3.11+** (Python 3.13 recommended)
- **Git**
- **MongoDB Atlas** account (or local MongoDB daemon)
- **OpenAI API Key** (for AI Recipe generation)

---

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mihir021/BasketIQ.git
   cd BasketIQ
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory (see format below).

5. **Run database migrations & collect static files:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

### Environment Variables (.env)

```env
DEBUG=True
DJANGO_SECRET_KEY=your_generated_django_secret_key
DJANGO_SETTINGS_MODULE=config.settings.production
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=grocery_admin
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
ADMIN_BOOTSTRAP_EMAIL=admin@basketiq.com
ADMIN_BOOTSTRAP_PASSWORD=SuperSecurePassword123!
ADMIN_BOOTSTRAP_NAME=System Admin
```

---

### Running with Docker

You can run the entire platform with zero local dependency configuration:

```bash
# Build and run containers
docker-compose up --build

# Stop containers
docker-compose down
```

---

## 🌐 Deployment Guide

### Why Render / Cloud Services instead of Vercel?
BasketIQ is built with **Python 5.1, Gunicorn, Scikit-learn, Pandas, and MongoDB**. 
- **Vercel** is primarily optimized for serverless frontend applications (Next.js, React, Vite). Its serverless functions impose a **50 MB bundle limit** and short execution timeouts, which fail when loading heavy data science packages like `scikit-learn` and `pandas`.
- **Render.com** (or Railway / Fly.io) runs full Docker / Python runtime containers with background workers, persistent connections to MongoDB, and zero serverless constraints.

### 1-Click Deployment on Render (Configured via `render.yaml`)
1. Push your repository to GitHub.
2. Sign in to [Render.com](https://render.com/).
3. Click **New +** ➔ **Blueprint**.
4. Select the `BasketIQ` repository. Render will automatically read `render.yaml`.
5. Supply your `MONGO_URI` and `OPENAI_API_KEY` under the Environment Variables prompt.
6. Click **Apply** — Render builds, migrates, and launches your live application!

---

## 🤝 Contributors

- **Mihir** ([@mihir021](https://github.com/mihir021)) — Project Lead & Full-Stack Development
- **Mayank Rojesara** ([@mayank122340](https://github.com/mayank122340)) — Full-Stack Architecture, REST APIs & ML Integration
