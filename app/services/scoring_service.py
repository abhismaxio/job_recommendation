"""
Scoring Service — Rule-based job-to-candidate match scorer.

Weights (total = 100):
  - Skills       : 50 pts  (must-have = hard filter, nice-to-have = bonus)
  - Experience   : 20 pts  (penalize below minimum, don't exclude)
  - Location     : 15 pts  (exact > remote > mismatch)
  - Salary       : 15 pts  (overlap between expected and job range)

Rationale:
  Skills are weighted highest (50%) because skill fit is the most direct
  indicator of job suitability. Experience is penalized rather than excluded
  to avoid discarding candidates who are slightly under the threshold but
  strong in all other dimensions — real hiring rarely hard-cuts on a single
  year of experience. Location and salary are weighted equally as secondary
  filters that affect candidate satisfaction more than raw capability.
"""

from app.models.candidate import Candidate
from app.models.job import Job

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
WEIGHT_SKILLS = 50
WEIGHT_EXPERIENCE = 20
WEIGHT_LOCATION = 15
WEIGHT_SALARY = 15


# ---------------------------------------------------------------------------
# Individual dimension scorers
# ---------------------------------------------------------------------------

def score_skills(candidate: Candidate, job: Job) -> tuple[float, str]:
    candidate_skills = {s.lower() for s in candidate.skills}

    must_haves = [s["skill"].lower() for s in job.required_skills if s["type"] == "must-have"]
    nice_to_haves = [s["skill"].lower() for s in job.required_skills if s["type"] == "nice-to-have"]

    missing_must_haves = [s for s in must_haves if s not in candidate_skills]
    if missing_must_haves:
        return 0.0, f"skills: 0/{WEIGHT_SKILLS} (missing must-have: {', '.join(missing_must_haves)})"

    if nice_to_haves:
        matched = sum(1 for s in nice_to_haves if s in candidate_skills)
        score = WEIGHT_SKILLS * (matched / len(nice_to_haves))
    else:
        score = float(WEIGHT_SKILLS)

    return round(score, 2), f"skills: {round(score, 1)}/{WEIGHT_SKILLS}"


def score_experience(candidate: Candidate, job: Job) -> tuple[float, str]:
    years = candidate.years_of_experience
    minimum = job.min_years_experience

    if minimum == 0 or years >= minimum:
        score = float(WEIGHT_EXPERIENCE)
    else:
        ratio = years / minimum
        score = WEIGHT_EXPERIENCE * ratio

    return round(score, 2), f"experience: {round(score, 1)}/{WEIGHT_EXPERIENCE}"


def score_location(candidate: Candidate, job: Job) -> tuple[float, str]:
    if candidate.location.lower() == job.location.lower():
        score = float(WEIGHT_LOCATION)
    elif job.remote_allowed:
        score = WEIGHT_LOCATION * 0.6
    else:
        score = 0.0

    return round(score, 2), f"location: {round(score, 1)}/{WEIGHT_LOCATION}"


def score_salary(candidate: Candidate, job: Job) -> tuple[float, str]:
    expected = candidate.expected_salary
    s_min = job.salary_min
    s_max = job.salary_max

    if s_max < expected:
        ratio = s_max / expected if expected > 0 else 0
        score = WEIGHT_SALARY * ratio * 0.1
    elif s_min > expected:
        score = float(WEIGHT_SALARY)
    else:
        score = float(WEIGHT_SALARY)

    return round(score, 2), f"salary: {round(score, 1)}/{WEIGHT_SALARY}"


def score_job_for_candidate(candidate: Candidate, job: Job) -> dict | None:
    skill_score, skill_breakdown = score_skills(candidate, job)

    if skill_score == 0 and any(s["type"] == "must-have" for s in job.required_skills):
        missing = [
            s["skill"].lower()
            for s in job.required_skills
            if s["type"] == "must-have" and s["skill"].lower() not in {x.lower() for x in candidate.skills}
        ]
        if missing:
            return None

    exp_score, exp_breakdown = score_experience(candidate, job)
    loc_score, loc_breakdown = score_location(candidate, job)
    sal_score, sal_breakdown = score_salary(candidate, job)

    total = round(skill_score + exp_score + loc_score + sal_score, 2)

    return {
        "job_id": job.id,
        "job_title": job.title,
        "score": total,
        "breakdown": {
            "skills": skill_breakdown,
            "experience": exp_breakdown,
            "location": loc_breakdown,
            "salary": sal_breakdown,
        },
    }


def rank_jobs_for_candidate(candidate: Candidate, jobs: list[Job], limit: int = 10) -> list[dict]:
    results = []
    for job in jobs:
        result = score_job_for_candidate(candidate, job)
        if result is not None:
            results.append(result)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]
