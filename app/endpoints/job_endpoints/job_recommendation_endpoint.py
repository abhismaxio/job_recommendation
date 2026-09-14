import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.candidate_service import get_all_candidates
from app.services.job_service import get_job
from app.services.scoring_service import score_job_for_candidate

router = APIRouter(tags=["Recommendations"])


@router.get("/{job_id}/recommendations")
async def get_job_recommendations(
    job_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = await get_all_candidates(db)

    results = []
    for candidate in candidates:
        result = score_job_for_candidate(candidate, job)
        if result is not None:
            results.append({
                "candidate_id": str(candidate.id),
                "candidate_name": candidate.name,
                "score": result["score"],
                "breakdown": result["breakdown"],
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "job_id": str(job_id),
        "job_title": job.title,
        "total_matches": len(results),
        "recommendations": results[:limit],
    }
