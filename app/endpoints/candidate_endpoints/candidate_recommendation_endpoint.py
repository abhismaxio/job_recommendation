from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.candidate_service import get_candidate
from app.services.job_service import get_all_jobs
from app.services.scoring_service import rank_jobs_for_candidate

router = APIRouter(tags=["Recommendations"])


@router.get("/{candidate_id}/recommendations")
async def get_candidate_recommendations(
    candidate_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    candidate = await get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    jobs = await get_all_jobs(db)
    ranked = rank_jobs_for_candidate(candidate, jobs, limit=limit)

    return {
        "candidate_id": candidate_id,
        "total_matches": len(ranked),
        "recommendations": ranked,
    }
