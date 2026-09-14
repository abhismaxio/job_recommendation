import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.postgres import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    skills = Column(ARRAY(String), nullable=False, default=[])
    years_of_experience = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    expected_salary = Column(Integer, nullable=False)
