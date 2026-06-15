# OptiFlow — Architecture Note

OptiFlow is an AI-powered Order Management System (OMS) specifically tailored for eyewear brands. It handles the complete lifecycle of a prescription eyewear order from intake to delivery, predicting SLA breaches using machine learning, and extracting prescription data using Vision LLMs.

## Tech Stack Overview

1. **Frontend**: React + Vite + Tailwind CSS + Lucide Icons + Recharts
2. **Backend**: FastAPI (Python 3.12)
3. **Database**: PostgreSQL (Relational Data & State Tracking)
4. **Caching & WebSockets**: Redis (Pub/Sub for real-time frontend updates)
5. **AI Vision Parsing**: Groq API (LLaVA-based vision model for Rx parsing)
6. **Machine Learning**: Scikit-Learn (Random Forest model for SLA breach prediction)
7. **Containerization**: Docker Compose (Multi-container architecture)

## Core Components

### 1. State Machine (The Order Lifecycle)
The core of OptiFlow is a strict, directed state machine that guarantees an order moves chronologically through production. The backend ensures that an order can only transition to valid subsequent states (e.g., `lab_production` -> `quality_control`). If an order fails QC, the state machine supports a explicit `loopback` to `lab_production` and increments the loopback counter, which heavily impacts the ML risk predictor.

### 2. AI Rx Parsing (Groq Vision)
When an image of a prescription card is uploaded, the FastAPI backend sends the image as a base64 string to the Groq Vision API. Using strict JSON Schema outputs, the AI extracts structured SPH, CYL, AXIS, and PD values for both the right and left eyes, calculating a confidence score for each field. Values with low confidence are highlighted for human review in the frontend UI.

### 3. Smart Inventory Matching
In `Phase 2`, the backend intercepts orders at the `inventory_check` stage and determines if the required lens blank (based on Type, Index, and Coatings) is available in-house. If it is, the SLA is set to 24 hours. If it must be procured externally, the SLA is extended to 72 hours, and the order is flagged as `external_procurement`.

### 4. Machine Learning TAT Predictor
A background worker (Asyncio task running within the FastAPI event loop) periodically scans active orders. It uses a trained Random Forest model (loaded via `joblib`) to predict the probability of an SLA breach. If the probability exceeds the threshold (0.6), the order's risk level is escalated to `AT_RISK` and a WebSocket event is fired to the frontend to update the Kanban board in real-time.

### 5. Real-Time Layer (WebSockets)
FastAPI maintains active WebSocket connections with the React frontend. When the state machine transitions an order, or the TAT Predictor changes a risk level, a message is published to Redis. All connected FastAPI instances subscribe to this Redis channel and broadcast the update to the connected browser clients, ensuring the Operations Dashboard is always perfectly in sync without aggressive polling.

## Deployment Strategy
The application is entirely containerized. Running `docker-compose up -d` spins up:
- **db**: PostgreSQL database (Port 5432)
- **redis**: Redis in-memory datastore (Port 6379)
- **backend**: FastAPI server & Background Workers (Port 8000)
- **frontend**: Nginx serving the built React Vite SPA (Port 3000 & 5173)

Configuration is managed securely via environment variables (e.g., `GROQ_API_KEY`, `DATABASE_URL`) injected dynamically at runtime.
