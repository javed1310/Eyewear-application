# OptiFlow — AI-Powered Order Management System

> AI-powered OMS purpose-built for eyewear brands. Tracks orders from intake through delivery, predicts SLA breaches, and manages lens inventory.

## Quick Start

### With Docker Compose (Recommended)
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Backend (FastAPI)** on http://localhost:8000
- **Frontend (React + Vite)** on http://localhost:5173

### Without Docker

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Project Structure

```
optiflow/
├── backend/           # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── core/      # Config, DB, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── api/       # Route handlers
│   │   ├── services/  # Business logic
│   │   └── workers/   # Background tasks
│   ├── ml/            # TAT prediction model
│   ├── seed/          # Demo data generator
│   └── tests/
├── frontend/          # React + Vite + Tailwind
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── hooks/
│       └── api/
└── docker-compose.yml
```

## Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ | Project Scaffolding |
| 1 | ⬜ | Core Data Model & State Machine |
| 2 | ⬜ | Inventory Matching & SLA |
| 3 | ⬜ | Dashboard Frontend |
| 4 | ⬜ | Real-Time WebSocket Layer |
| 5 | ⬜ | AI Rx Parsing & Cross-Check |
| 6 | ⬜ | TAT Prediction & Breach Alerts |
| 7 | ⬜ | Auth, Polish & Deployment |
