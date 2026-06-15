# Stage 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
ENV VITE_API_URL=""
RUN npm run build

# Stage 2: Build the FastAPI Backend
FROM python:3.12-slim
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build from Stage 1 into the backend's static folder
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose the port Render expects
EXPOSE 10000

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV PORT=10000

# Run migrations and start Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
