import uuid

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.postgres import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)

    # List of {"skill": "Python", "type": "must-have" | "nice-to-have"}
    required_skills = Column(JSONB, nullable=False, default=[])

    min_years_experience = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    remote_allowed = Column(Boolean, nullable=False, default=False)

    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
