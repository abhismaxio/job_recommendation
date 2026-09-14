from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.postgres import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    skills = Column(ARRAY(String), nullable=False, default=[])
    years_of_experience = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    expected_salary = Column(Integer, nullable=False)
