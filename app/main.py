from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import Base, engine, get_db
import app.models.candidate  # noqa: F401 — register models with Base
import app.models.job  # noqa: F401 — register models with Base

# Commands (Write)
from app.endpoints.candidate_endpoints import candidate_endpoint
from app.endpoints.job_endpoints import job_endpoint

# Queries (Read)
from app.endpoints.candidate_endpoints import candidate_recommendation_endpoint
from app.endpoints.job_endpoints import job_recommendation_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — create all tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# CQRS — Commands
app.include_router(candidate_endpoint.router, prefix="/candidates")
app.include_router(job_endpoint.router, prefix="/jobs")

# CQRS — Queries
app.include_router(candidate_recommendation_endpoint.router, prefix="/candidates")
app.include_router(job_recommendation_endpoint.router, prefix="/jobs")


@app.get("/")
def read_root():
    return {"message": "Welcome to Job Recommendation API"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
