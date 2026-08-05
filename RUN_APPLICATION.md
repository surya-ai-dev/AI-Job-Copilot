# Running the AI Job Copilot Application

This guide contains everything needed to clone the repository, install dependencies, configure environment settings, run the backend and frontend services, and verify deployment status.

---

## 1. Project Overview

AI Job Copilot is an AI-powered SaaS platform that helps job seekers tailor applications and draft outreach emails.

### Tech Stack
*   **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, Alembic, Uvicorn, pytest.
*   **Frontend**: Node.js, Next.js, React, TypeScript, Tailwind CSS.
*   **AI Engine**: Gemini Pro model API routes.
*   **OAuth**: Google OAuth 2.0 Gmail APIs integration.

---

## 2. Prerequisites

Verify installation of the following prerequisites before starting the stack:

| Component | Target Version | Verification Command |
| :--- | :--- | :--- |
| **Python** | 3.10+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **Docker** | 20+ | `docker --version` |
| **PostgreSQL**| 15+ | `psql --version` |
| **Redis** | 7+ | `redis-server --version` |

---

## 3. Environment Variables

Create a `.env` file in the `backend/` directory using the following configurations:

```env
# backend/.env
APP_ENV=development
APP_SECRET_KEY=secure-jwt-signing-secret-key-string-here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=jobcopilot_db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/0
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
```

---

## 4. Project Structure

*   `backend/`: FastAPI application code (domain, models, repositories, endpoints).
*   `frontend/`: Next.js client workspace screens and assets.
*   `database/migrations/`: Alembic DDL schema migration files.
*   `storage/`: Mount location for PDFs and temporary uploads.

---

## 5. Installation Steps

### Backend Installation

```bash
# Clone the repository
git clone https://github.com/example/jobcopilot_ai.git
cd jobcopilot_ai

# Setup virtual environment
# Windows:
python -v venv venv
.\venv\Scripts\activate

# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Frontend Installation

```bash
cd frontend
npm install
```

---

## 6. Database Setup

Ensure PostgreSQL is running locally, then initialize the database schema:

```bash
# Create database
createdb -U postgres jobcopilot_db

# Run Alembic migrations
cd ..
alembic upgrade head
```

---

## 7. Redis Setup

Ensure Redis is running locally:

```bash
# Verify connection
redis-cli ping
# Expected response: PONG
```

---

## 8. Running the Backend

```bash
# Windows/macOS/Linux:
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Expected output:
```text
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 9. Running the Frontend

```bash
cd frontend
npm run dev
```
Expected output:
```text
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## 10. Docker Setup

If you prefer deploying using Docker Compose:

```bash
# Build and run containers
docker-compose up --build -d

# View container logs
docker-compose logs -f

# Stop containers
docker-compose down
```

---

## 11. Health Checks

Confirm system connectivity by querying health check endpoints:

*   **API Health Probes**: `GET http://127.0.0.1:8000/health/api`
    *   Expected response: `{"status": "healthy"}`
*   **System Metrics Probes**: `GET http://127.0.0.1:8000/api/v1/health/metrics`
    *   Expected response:
    ```json
    {
      "status": "healthy",
      "timestamp": 1722791400.0,
      "metrics": {
        "cpu_usage_percent": 12.5,
        "memory_usage_percent": 64.2,
        "disk_free_gb": 120,
        "disk_usage_percent": 35.4
      },
      "dependencies": {
        "database": "connected",
        "redis_cache": "connected"
      }
    }
    ```

---

## 12. Running Tests

```bash
# Run pytest test suite
pytest
```

---

## 13. API Testing

### Swagger UI Documentation
Access documentation dynamically via your browser:
*   Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### curl Example Request
```bash
curl -X GET http://127.0.0.1:8000/health/api
```

---

## 14. Common Problems & Solutions

#### Problem: Port 8000 already in use
*   **Cause**: Another backend instance or API process is running.
*   **Solution**: Kill the process using port 8000:
    ```bash
    # Windows:
    netstat -ano | findstr 8000
    taskkill /PID <PID> /F
    
    # macOS/Linux:
    lsof -i :8000
    kill -9 <PID>
    ```

#### Problem: Database Connection Refused
*   **Cause**: PostgreSQL service is stopped or host configs in `.env` are wrong.
*   **Solution**: Check your database settings and confirm PostgreSQL is running.

---

## 15. Logging

*   **Local Backend logs**: Outputs stdout in structured JSON format.
*   **Docker Logs**: Run `docker-compose logs -f [service_name]` (e.g. `docker-compose logs -f backend`).

---

## 16. Debugging Guide

*   Use standard IDE debugging configurations (VS Code `launch.json` or PyCharm run setups) referencing Uvicorn.
*   Use browser consoles to trace frontend React hooks.

---

## 17. Development Workflow

1.  Start local database and cache (PostgreSQL & Redis).
2.  Activate Python virtual environment and run migrations.
3.  Launch FastAPI server.
4.  Launch Next.js development server.
5.  Execute `pytest` to verify stability before commit changes.

---

## 18. Verification Checklist

- [ ] Backend is running.
- [ ] Frontend page resolves.
- [ ] Database migrations are applied.
- [ ] Health status endpoint returns status healthy.
- [ ] User authentication handles registration and login checks.

---

## 19. Production Notes

*   **SSL Termination**: Ensure HTTPS certificates are enabled using Nginx reverse proxy rules.
*   **Environment Variables**: Rotate JWT signing keys and Gemini keys in target secrets managers.
*   **Caching Expirations**: Cache dashboard stats summaries to reduce database reads load.

---

## 20. Final Quick Start

Get up and running in under a minute using Docker Compose:

```bash
# Clone and cd
git clone https://github.com/example/jobcopilot_ai.git
cd jobcopilot_ai

# Setup environment
cp .env.example .env

# Start stack
docker-compose up --build -d
```
Your frontend is ready on [http://localhost](http://localhost) and backend on [http://localhost/api/v1](http://localhost/api/v1).
