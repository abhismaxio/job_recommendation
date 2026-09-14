from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


async def insert_job(db: AsyncSession, data: dict) -> Job:
    job = Job(
        title=data["title"],
        required_skills=data["required_skills"],
        min_years_experience=data["min_years_experience"],
        location=data["location"],
        remote_allowed=data.get("remote_allowed", False),
        salary_min=data["salary_min"],
        salary_max=data["salary_max"],
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def fetch_job(db: AsyncSession, job_id: int) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def fetch_all_jobs(db: AsyncSession) -> list[Job]:
    result = await db.execute(select(Job))
    return result.scalars().all()
