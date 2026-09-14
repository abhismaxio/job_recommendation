from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.db.candidate_db import fetch_candidate
from app.db.job_db import fetch_all_jobs
from app.services.scoring_service import (
    rank_jobs_for_candidate,
    Weights,
    WEIGHT_SKILLS,
    WEIGHT_EXPERIENCE,
    WEIGHT_LOCATION,
    WEIGHT_SALARY,
)

router = APIRouter(tags=["Recommendations"])


@router.get("/{candidate_id}/recommendations", status_code=200)
async def get_candidate_recommendations(
    candidate_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    weight_skills: int = Query(default=WEIGHT_SKILLS, ge=0, le=100, description="Weight for skills (default 50)"),
    weight_experience: int = Query(default=WEIGHT_EXPERIENCE, ge=0, le=100, description="Weight for experience (default 20)"),
    weight_location: int = Query(default=WEIGHT_LOCATION, ge=0, le=100, description="Weight for location (default 15)"),
    weight_salary: int = Query(default=WEIGHT_SALARY, ge=0, le=100, description="Weight for salary (default 15)"),
    db: AsyncSession = Depends(get_db),
):
    try:
        total_weight = weight_skills + weight_experience + weight_location + weight_salary
        if total_weight != 100:
            raise HTTPException(status_code=400, detail=f"Total weight must equal exactly 100. Current total is {total_weight}.")

        candidate = await fetch_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        weights = Weights(
            skills=weight_skills,
            experience=weight_experience,
            location=weight_location,
            salary=weight_salary,
        )

        jobs = await fetch_all_jobs(db)
        ranked = rank_jobs_for_candidate(candidate, jobs, limit=limit, weights=weights)

        return {
            "candidate_id": candidate_id,
            "weights_used": {
                "skills": weight_skills,
                "experience": weight_experience,
                "location": weight_location,
                "salary": weight_salary,
            },
            "total_matches": len(ranked),
            "recommendations": ranked,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred while fetching recommendations.")
