from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.db.job_db import insert_job

router = APIRouter(tags=["Jobs"])


class RequiredSkill(BaseModel):
    skill: str
    type: str  # "must-have" or "nice-to-have"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("must-have", "nice-to-have"):
            raise ValueError('type must be "must-have" or "nice-to-have"')
        return v


class JobCreate(BaseModel):
    title: str
    required_skills: list[RequiredSkill]
    min_years_experience: int
    location: str
    remote_allowed: bool = False
    salary_min: int
    salary_max: int


@router.post("/", status_code=201)
async def create_job_endpoint(
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    job = await insert_job(db, data)
    return {
        "id": job.id,
        "title": job.title,
        "required_skills": job.required_skills,
        "min_years_experience": job.min_years_experience,
        "location": job.location,
        "remote_allowed": job.remote_allowed,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
    }
