from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.db.candidate_db import fetch_all_candidates
from app.db.job_db import fetch_job
from app.services.scoring_service import (
    score_job_for_candidate,
    Weights,
    WEIGHT_SKILLS,
    WEIGHT_EXPERIENCE,
    WEIGHT_LOCATION,
    WEIGHT_SALARY,
)

router = APIRouter(tags=["Recommendations"])


@router.get("/{job_id}/recommendations", status_code=200)
async def get_job_recommendations(
    job_id: int,
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

        job = await fetch_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        weights = Weights(
            skills=weight_skills,
            experience=weight_experience,
            location=weight_location,
            salary=weight_salary,
        )

        candidates = await fetch_all_candidates(db)

        results = []
        for candidate in candidates:
            result = score_job_for_candidate(candidate, job, weights)
            if result is not None:
                results.append({
                    "candidate_id": candidate.id,
                    "candidate_name": candidate.name,
                    "score": result["score"],
                    "max_score": result["max_score"],
                    "breakdown": result["breakdown"],
                })

        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "job_id": job_id,
            "job_title": job.title,
            "weights_used": {
                "skills": weight_skills,
                "experience": weight_experience,
                "location": weight_location,
                "salary": weight_salary,
            },
            "total_matches": len(results),
            "recommendations": results[:limit],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred while fetching recommendations.")
