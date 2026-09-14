from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.db.candidate_db import insert_candidate

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
    try:
        candidate = await insert_candidate(db, payload.model_dump())
        return {
            "id": candidate.id,
            "name": candidate.name,
            "skills": candidate.skills,
            "years_of_experience": candidate.years_of_experience,
            "location": candidate.location,
            "expected_salary": candidate.expected_salary,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred while creating candidate: {str(e)}")
