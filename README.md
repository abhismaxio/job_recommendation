# Job Recommendation Engine

A rule-based Job Match API that recommends jobs to candidates based on skill, experience, location, and salary fit.

---

## How to Run Locally

### Prerequisites
- Python 3.12+
- Docker & Docker Compose

---

### Option 1: Docker (Recommended)

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd job_recommendation
   ```

2. **Set up environment variables**
   ```bash
   cp .example.env .env
   ```

3. **Start the API + Postgres**
   ```bash
   docker-compose up --build
   ```

4. **Verify it's running**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {"status": "ok", "database": "connected"}
   ```

5. **API docs** available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Run Locally (without Docker)

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd job_recommendation
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .example.env .env
   # Update DATABASE_URL in .env to point to your local Postgres instance
   ```

5. **Start the API**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **API docs** available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
job_recommendation/
├── app/
│   ├── core/
│   │   └── config.py        # Settings loaded from .env
│   ├── db/
│   │   └── postgres.py      # Async SQLAlchemy engine & session
│   ├── endpoints/           # Route handlers
│   ├── models/              # ORM models
│   ├── services/            # Business logic & scoring
│   └── main.py              # FastAPI app entrypoint
├── .example.env             # Example environment variables
├── Dockerfile               # API Docker image
├── docker-compose.yml       # API + Postgres services
└── README.md
```

---

## Environment Variables

| Variable        | Description                        | Default                                                                 |
|-----------------|------------------------------------|-------------------------------------------------------------------------|
| `POSTGRES_USER` | Postgres username                  | `postgres`                                                              |
| `POSTGRES_PASSWORD` | Postgres password              | `postgres`                                                              |
| `POSTGRES_DB`   | Postgres database name             | `job_recommendation`                                                    |
| `DATABASE_URL`  | Full async DB connection string    | `postgresql+asyncpg://postgres:postgres@localhost:5432/job_recommendation` |