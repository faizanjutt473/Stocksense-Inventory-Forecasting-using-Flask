# StockSense: Smart Inventory & Demand Forecasting System

A full-stack Flask application that helps retail shops avoid both stock-outs and overstock. It manages products, suppliers, purchase orders and stock movements, raises low-stock alerts with reorder suggestions, and forecasts future demand from sales history using Prophet and XGBoost.

## Features

- **Inventory management:** products, suppliers, purchase orders, stock in/out with full history
- **Low-stock alerts** and automatic **reorder suggestions**
- **Demand forecasting** (Prophet / XGBoost) running as background jobs with Celery
- **Barcode and QR support:** SKU lookup plus generated Code128 and QR images
- **Reports:** profit by category, fast-moving items, dead stock
- **Admin dashboard** with Chart.js charts, light/dark theme, responsive layout
- **REST API** with interactive Swagger docs, protected by admin login

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-RESTX, Flask-Login |
| Database | PostgreSQL |
| Background jobs | Celery, Redis |
| Forecasting | Prophet, XGBoost, pandas, scikit-learn |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| DevOps | Docker, Docker Compose, Gunicorn |

## Project Structure

```
Stocksense/
├── Backend/
│   ├── app/
│   │   ├── api/        # REST API (Flask-RESTX)
│   │   ├── models/     # SQLAlchemy models
│   │   ├── services/   # analytics and forecasting logic
│   │   └── tasks/      # Celery tasks
│   ├── config.py
│   ├── run.py
│   ├── seed.py         # demo data
│   └── celery_worker.py
├── Frontend/           # 8 linked pages + login (HTML, CSS, JS)
├── Dockerfile
└── docker-compose.yml
```

## Quick Start with Docker

1. Copy `.env.example` to `.env` and set your own values.
2. Build and start everything:
   ```bash
   docker compose up --build
   ```
3. In a second terminal, add demo data and create an admin user:
   ```bash
   docker compose exec web python seed.py
   docker compose exec web flask create-admin
   ```
4. Open http://localhost:5000 and log in.

## Run Locally (without Docker)

Requirements: Python 3.12, PostgreSQL, Redis.

```bash
cd Backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

1. Create a database named `stocksense_db` in PostgreSQL.
2. Copy `Backend/.env.example` to `Backend/.env` and fill in your values.
3. Create tables, demo data and an admin user:
   ```bash
   flask db upgrade
   python seed.py
   flask create-admin
   ```
4. Start the services (three terminals):
   ```bash
   python run.py
   celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
   ```
   Redis must be running (for example: `docker run -d -p 6379:6379 redis:7`).
5. Open http://127.0.0.1:5000

## API Documentation

Interactive Swagger docs are available at `/api/docs` after logging in.

## Roadmap

- LSTM forecasting model
- Camera-based barcode scanning
- Multi-user roles and permissions

## Author

Muhammad Faizan Farooq. [GitHub](https://github.com/faizanjutt473)