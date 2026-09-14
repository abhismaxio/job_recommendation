from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db

from app.endpoints.insert_endpoints import candidate_endpoint, job_endpoint



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)


app.include_router(candidate_endpoint.router, prefix="/candidates")
app.include_router(job_endpoint.router, prefix="/jobs")




@app.get("/")
def read_root():
    return {"message": "Welcome to Job Recommendation API"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
