from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.candidate_service import create_candidate

router = APIRouter(tags=["Candidates"])


class CandidateCreate(BaseModel):
    name: str
    skills: list[str]
    years_of_experience: int
    location: str
    expected_salary: int


@router.post("/", status_code=201)
async def create_candidate_endpoint(
    payload: CandidateCreate,
    db: AsyncSession = Depends(get_db),
):
    candidate = await create_candidate(db, payload.model_dump())
    return {
        "id": str(candidate.id),
        "name": candidate.name,
        "skills": candidate.skills,
        "years_of_experience": candidate.years_of_experience,
        "location": candidate.location,
        "expected_salary": candidate.expected_salary,
    }
