from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate


async def create_candidate(db: AsyncSession, data: dict) -> Candidate:
    candidate = Candidate(
        name=data["name"],
        skills=data["skills"],
        years_of_experience=data["years_of_experience"],
        location=data["location"],
        expected_salary=data["expected_salary"],
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def get_candidate(db: AsyncSession, candidate_id: int) -> Candidate | None:
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    return result.scalar_one_or_none()


async def get_all_candidates(db: AsyncSession) -> list[Candidate]:
    result = await db.execute(select(Candidate))
    return result.scalars().all()
