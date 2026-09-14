# Job Recommendation Engine

A transparent, rule-based **Job Match API** that recommends jobs to candidates based on skill fit, experience, location, and salary compatibility. Every score is fully explainable — no black-box ML, just clear weighted logic.

---

## Table of Contents

1. [How to Run](#how-to-run)
2. [API Endpoints](#api-endpoints)
3. [Scoring Formula & Weight Rationale](#scoring-formula--weight-rationale)
4. [Configurable Weights](#configurable-weights)
5. [Assumptions & What I'd Do Differently](#assumptions--what-id-do-differently)
6. [AI Tool Usage](#ai-tool-usage)
7. [Running Tests](#running-tests)
8. [Project Structure](#project-structure)
9. [Environment Variables](#environment-variables)

---

## How to Run

### Option 1: Docker (Recommended)

**Prerequisites:** Docker & Docker Compose installed.

```bash
# 1. Clone the repo
git clone <repo-url>
cd job_recommendation

# 2. Set up environment variables
cp .example.env .env

# 3. Start API + Postgres
docker-compose up --build

# 4. Verify
curl http://localhost:8000/health
# → {"status": "ok", "database": "connected"}
```

**API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

> Tables are auto-created on startup via SQLAlchemy `create_all`. No manual migration step needed for a fresh database.

---

### Option 2: Run Locally (without Docker)

**Prerequisites:** Python 3.12+, a running Postgres instance.

```bash
# 1. Clone the repo
git clone <repo-url>
cd job_recommendation

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .example.env .env
# Edit .env — update DATABASE_URL to point to your local Postgres

# 5. Start the API
uvicorn app.main:app --reload
```

**API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/candidates/` | Create a candidate profile |
| `POST` | `/jobs/` | Create a job posting |
| `GET` | `/candidates/{id}/recommendations` | Ranked jobs for a candidate |
| `GET` | `/jobs/{id}/recommendations` | Best-fit candidates for a job *(bonus)* |
| `GET` | `/health` | DB connectivity check |

### Query Parameters (recommendation endpoints)

| Param | Default | Description |
|-------|---------|-------------|
| `limit` | `10` | Top-N results to return |
| `weight_skills` | `50` | Weight for skill scoring |
| `weight_experience` | `20` | Weight for experience scoring |
| `weight_location` | `15` | Weight for location scoring |
| `weight_salary` | `15` | Weight for salary scoring |

---

## Scoring Formula & Weight Rationale

> This is the core of the system. Every recommendation score is the sum of four independently computed dimensions.

### Formula

```
total_score = skills_score + experience_score + location_score + salary_score
```

### Default Weights

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| **Skills** | 50 | Skill fit is the strongest predictor of job suitability. A candidate who can't do the job is not a match regardless of other factors. |
| **Experience** | 20 | Years of experience matter but are not a hard gate — a highly skilled candidate slightly under the threshold is still valuable. |
| **Location** | 15 | Location affects logistics and culture fit but is increasingly flexible with remote work. |
| **Salary** | 15 | Salary misalignment causes early attrition. Important, but a candidate may negotiate, so it's not a hard filter. |

### Dimension Details

#### Skills (50 pts)
- **Must-have skills** → **Hard filter**: if the candidate is missing _any_ must-have skill, the job is excluded from results entirely, regardless of all other scores.
- **Nice-to-have skills** → Proportional boost: `(matched_nice_to_haves / total_nice_to_haves) × 50`
- If the job has no required skills at all → full 50 pts.

#### Experience (20 pts)
- Candidate meets or exceeds `minYearsExperience` → **full 20 pts**
- Candidate below minimum → `(candidate_years / min_years) × 20` — **linear penalty**

  **Why penalize instead of exclude?**
  Real hiring rarely hard-cuts on a single year of experience. A candidate with 4 years applying for a 5-year role is still a strong candidate if their skills, location, and salary align. Excluding them would create false negatives. The penalty is proportional and transparent — reviewers can see the experience score in the breakdown and decide.

#### Location (15 pts)
- Exact city match → **15 pts**
- No exact match, but `remoteAllowed = true` → **9 pts** (60%)
- No match, no remote → **0 pts**

#### Salary (15 pts)
- `expectedSalary` within job's `[salary_min, salary_max]` → **15 pts**
- Job's `salary_min > expectedSalary` (job pays more than expected) → **15 pts** (best case for candidate)
- Job's `salary_max < expectedSalary` → near zero: `(salary_max / expected) × 0.1 × 15`

  Near-zero (not exactly zero) preserves ranking signal for edge cases where everything else is a strong match.

### Example Breakdown

```
Candidate: Alice, Python + PostgreSQL, 4 yrs, NYC, $110k expected
Job: Backend Engineer, Python (must-have) + Docker (nice-to-have), 3 yrs min, NYC, $90k–$130k

skills:     50/50  → Python present (must-have ✓), Docker present (nice-to-have ✓, 1/1 = 100%)
experience: 20/20  → 4 yrs >= 3 yrs min
location:   15/15  → NYC == NYC
salary:     15/15  → $110k within [$90k–$130k]

total: 100/100
```

---

## Configurable Weights

Weights are **not hardcoded** — they can be overridden per request via query parameters:

```bash
# Skill-heavy hiring (senior technical role)
GET /candidates/1/recommendations?weight_skills=70&weight_experience=20&weight_location=5&weight_salary=5

# Remote-first company — location irrelevant
GET /candidates/1/recommendations?weight_skills=50&weight_experience=25&weight_location=0&weight_salary=25

# Salary-sensitive role
GET /candidates/1/recommendations?weight_skills=40&weight_experience=20&weight_location=10&weight_salary=30
```

The response always includes a `weights_used` field so the caller can verify what was applied.

---

## Assumptions & What I'd Do Differently

### Assumptions Made

- **Skills are plain strings** — no normalization (e.g., "JS" and "JavaScript" are treated as different skills). A real system would use a skill taxonomy or synonym map.
- **Single location per candidate/job** — no support for multi-location jobs or candidates willing to relocate.
- **Expected salary is a single number** — candidates don't express a range. In reality, salary expectations are negotiable.
- **Auto-incrementing integer IDs** — kept simple for easy testing. A production system would use UUIDs for public-facing IDs.
- **`create_all` on startup** — acceptable for a new DB; a production system would use Alembic migrations to safely evolve the schema.

### What I'd Do Differently With More Time

- **Alembic migrations** — for safe, versioned schema changes in production.
- **Skill normalization** — a synonym map or embedding-based matching to handle "JS" vs "JavaScript".
- **Pagination** — the current `limit` param is a top-N filter but doesn't support offset-based pagination.
- **Caching** — scoring all jobs for every request is O(n). With many jobs, a cache layer (Redis) would help.
- **More test coverage** — integration tests with a test DB, not just unit tests on mocks.
- **Structured logging** — replace `print` statements with proper structured logs.

---

## AI Tool Usage

This project was built with significant AI coding assistance using **Antigravity IDE (powered by Gemini)**. I used it as a pair programmer throughout — not just for boilerplate, but for design discussions and code generation.

**What AI generated:**
- FastAPI app setup, lifespan, and router registration in `main.py`
- SQLAlchemy model definitions for `Candidate` and `Job`
- `Dockerfile` and `docker-compose.yml` configuration
- The initial structure of the scoring service (function signatures, dimension breakdown pattern)
- Pydantic request/response schemas in the endpoint files
- The full `test_scoring.py` test file including edge case enumeration

**Where I made decisions and overrides:**
- **ID type:** AI defaulted to UUID primary keys. I switched to auto-incrementing integers — easier to use during manual testing (`GET /candidates/1/recommendations` beats copying a UUID).
- **Folder structure:** AI initially created `insert_endpoints/` and `fetch_endpoints/`. I restructured to `candidate_endpoints/` and `job_endpoints/` — domain-driven grouping is more intuitive than operation-type grouping.
- **`__init__.py` files:** AI added them automatically. I removed them — Python 3.3+ namespace packages don't require them, and they add unnecessary noise.
- **CQRS pattern:** I explicitly asked for CQRS-style separation in `main.py` and shaped how commands vs queries are registered.
- **Salary scoring formula:** The AI's first version gave binary pass/fail (full score or zero). I changed it to a graduated near-zero penalty (`salary_max / expected × 0.1 × weight`) — this preserves ranking signal so a job that nearly meets salary still appears below a perfect match rather than disappearing entirely.
- **Scoring weights:** AI suggested equal weights. I redistributed — skills at 50% reflects real hiring where technical fit dominates; experience penalized not excluded reflects how actual hiring managers think.

---

## Running Tests

Tests cover all scoring logic edge cases with no database dependency (uses `SimpleNamespace` mocks).

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest app/tests/test_scoring.py -v
```

**Key edge cases tested:**
- Candidate missing a must-have skill → excluded from results (`None` returned)
- Partial nice-to-have match → proportional boost
- Candidate below minimum experience → linear penalty, not exclusion
- Job salary max below expectation → near-zero score
- Full perfect match → score of 100
- Limit query param → correct top-N returned

---

## Project Structure

```
job_recommendation/
├── app/
│   ├── core/
│   │   ├── config.py                          # Settings from .env (pydantic-settings)
│   │   └── postgres.py                        # Async SQLAlchemy engine, session, Base
│   ├── db/
│   │   ├── candidate_db.py                    # Candidate DB operations
│   │   └── job_db.py                          # Job DB operations
│   ├── endpoints/
│   │   ├── candidate_endpoints/
│   │   │   ├── candidate_endpoint.py          # POST /candidates/
│   │   │   └── candidate_recommendation_endpoint.py  # GET /candidates/{id}/recommendations
│   │   └── job_endpoints/
│   │       ├── job_endpoint.py                # POST /jobs/
│   │       └── job_recommendation_endpoint.py # GET /jobs/{id}/recommendations
│   ├── models/
│   │   ├── candidate.py                       # Candidate ORM model
│   │   └── job.py                             # Job ORM model
│   ├── services/
│   │   └── scoring_service.py                 # Rule-based scoring engine
│   ├── tests/
│   │   └── test_scoring.py                    # Pytest scoring tests (26 cases)
│   └── main.py                                # FastAPI app, lifespan, CQRS router registration
├── .example.env                               # Example environment variables
├── .gitignore
├── Dockerfile                                 # API image (Python 3.12 slim)
├── docker-compose.yml                         # API + Postgres 16
├── requirements.txt
└── README.md
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Postgres username | `postgres` |
| `POSTGRES_PASSWORD` | Postgres password | `postgres` |
| `POSTGRES_DB` | Postgres database name | `job_recommendation` |
| `DATABASE_URL` | Full async DB connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/job_recommendation` |