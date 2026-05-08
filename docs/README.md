# BasketIQ

BasketIQ is a Django-based grocery platform organized for production deployment and long-term growth.

## Structure

- `apps/accounts/` handles authentication and profile flows.
- `apps/market/` contains the catalogue, pricing, and product APIs.
- `apps/planner/` powers AI meal-planning flows.
- `apps/orders/` owns cart and order history behavior.
- `apps/expenses/` exposes expense tracking analytics.
- `config/settings/` provides split settings for base, development, and production.
- `static/`, `templates/`, `tests/`, `scripts/`, and `docs/` are centralized at the project root.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Install development dependencies with `pip install -r requirements/development.txt`.
3. Run migrations with `python manage.py migrate`.
4. Start the app with `python manage.py runserver`.
5. Run tests with `pytest`.

## Deployment

- Use `config.settings.production` for deployed environments.
- Build the container with the included `Dockerfile`.
- `docker-compose.yml` provisions the Django app, PostgreSQL, and Kafka services.
