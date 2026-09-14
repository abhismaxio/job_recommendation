"""
Tests for the scoring service.

We use simple mock objects (SimpleNamespace) to simulate Candidate and Job
models without needing a real database connection.

Edge cases covered:
  - Candidate missing a must-have skill (hard filter)
  - Candidate missing all nice-to-have skills
  - Candidate with all nice-to-have skills
  - Candidate below min experience (penalized)
  - Candidate at exactly min experience
  - Exact location match
  - Remote allowed but different location
  - Location mismatch, no remote
  - Salary: job max below expectation (near zero)
  - Salary: expected within range (full score)
  - Salary: job pays more than expected (full score)
  - Full match — all dimensions score max
  - Full mismatch — filtered out by must-have
"""

from types import SimpleNamespace

import pytest

from app.services.scoring_service import (
    rank_jobs_for_candidate,
    score_experience,
    score_job_for_candidate,
    score_location,
    score_salary,
    score_skills,
    WEIGHT_EXPERIENCE,
    WEIGHT_LOCATION,
    WEIGHT_SALARY,
    WEIGHT_SKILLS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_candidate(skills, years, location, salary):
    return SimpleNamespace(
        skills=skills,
        years_of_experience=years,
        location=location,
        expected_salary=salary,
    )


def make_job(required_skills, min_years, location, remote, salary_min, salary_max, title="Test Job", id=1):
    return SimpleNamespace(
        id=id,
        title=title,
        required_skills=required_skills,
        min_years_experience=min_years,
        location=location,
        remote_allowed=remote,
        salary_min=salary_min,
        salary_max=salary_max,
    )


# ---------------------------------------------------------------------------
# Skills scoring
# ---------------------------------------------------------------------------

class TestScoreSkills:

    def test_missing_must_have_returns_zero(self):
        candidate = make_candidate(["JavaScript"], 3, "NYC", 80000)
        job = make_job([{"skill": "Python", "type": "must-have"}], 2, "NYC", False, 70000, 100000)
        score, breakdown = score_skills(candidate, job)
        assert score == 0.0
        assert "missing must-have" in breakdown

    def test_all_must_haves_present_no_nice_to_have(self):
        candidate = make_candidate(["Python", "PostgreSQL"], 3, "NYC", 80000)
        job = make_job(
            [{"skill": "Python", "type": "must-have"}, {"skill": "PostgreSQL", "type": "must-have"}],
            2, "NYC", False, 70000, 100000
        )
        score, _ = score_skills(candidate, job)
        assert score == WEIGHT_SKILLS

    def test_no_required_skills_gives_full_score(self):
        candidate = make_candidate(["Python"], 3, "NYC", 80000)
        job = make_job([], 2, "NYC", False, 70000, 100000)
        score, _ = score_skills(candidate, job)
        assert score == WEIGHT_SKILLS

    def test_nice_to_have_partial_match(self):
        candidate = make_candidate(["Docker"], 3, "NYC", 80000)
        job = make_job(
            [{"skill": "Docker", "type": "nice-to-have"}, {"skill": "Redis", "type": "nice-to-have"}],
            2, "NYC", False, 70000, 100000
        )
        score, _ = score_skills(candidate, job)
        assert score == WEIGHT_SKILLS * 0.5

    def test_nice_to_have_none_matched(self):
        candidate = make_candidate(["Java"], 3, "NYC", 80000)
        job = make_job(
            [{"skill": "Docker", "type": "nice-to-have"}, {"skill": "Redis", "type": "nice-to-have"}],
            2, "NYC", False, 70000, 100000
        )
        score, _ = score_skills(candidate, job)
        assert score == 0.0

    def test_skills_case_insensitive(self):
        candidate = make_candidate(["python", "POSTGRESQL"], 3, "NYC", 80000)
        job = make_job([{"skill": "Python", "type": "must-have"}], 2, "NYC", False, 70000, 100000)
        score, _ = score_skills(candidate, job)
        assert score == WEIGHT_SKILLS


# ---------------------------------------------------------------------------
# Experience scoring
# ---------------------------------------------------------------------------

class TestScoreExperience:

    def test_meets_minimum_gives_full_score(self):
        candidate = make_candidate(["Python"], 5, "NYC", 80000)
        job = make_job([], 5, "NYC", False, 70000, 100000)
        score, _ = score_experience(candidate, job)
        assert score == WEIGHT_EXPERIENCE

    def test_exceeds_minimum_gives_full_score(self):
        candidate = make_candidate(["Python"], 8, "NYC", 80000)
        job = make_job([], 5, "NYC", False, 70000, 100000)
        score, _ = score_experience(candidate, job)
        assert score == WEIGHT_EXPERIENCE

    def test_below_minimum_penalized(self):
        candidate = make_candidate(["Python"], 2, "NYC", 80000)
        job = make_job([], 4, "NYC", False, 70000, 100000)
        score, _ = score_experience(candidate, job)
        assert score == WEIGHT_EXPERIENCE * (2 / 4)

    def test_zero_minimum_gives_full_score(self):
        candidate = make_candidate(["Python"], 0, "NYC", 80000)
        job = make_job([], 0, "NYC", False, 70000, 100000)
        score, _ = score_experience(candidate, job)
        assert score == WEIGHT_EXPERIENCE


# ---------------------------------------------------------------------------
# Location scoring
# ---------------------------------------------------------------------------

class TestScoreLocation:

    def test_exact_match_gives_full_score(self):
        candidate = make_candidate([], 3, "New York", 80000)
        job = make_job([], 2, "New York", False, 70000, 100000)
        score, _ = score_location(candidate, job)
        assert score == WEIGHT_LOCATION

    def test_location_case_insensitive(self):
        candidate = make_candidate([], 3, "new york", 80000)
        job = make_job([], 2, "New York", False, 70000, 100000)
        score, _ = score_location(candidate, job)
        assert score == WEIGHT_LOCATION

    def test_remote_allowed_gives_partial_score(self):
        candidate = make_candidate([], 3, "Chicago", 80000)
        job = make_job([], 2, "New York", True, 70000, 100000)
        score, _ = score_location(candidate, job)
        assert score == WEIGHT_LOCATION * 0.6

    def test_mismatch_no_remote_gives_zero(self):
        candidate = make_candidate([], 3, "Chicago", 80000)
        job = make_job([], 2, "New York", False, 70000, 100000)
        score, _ = score_location(candidate, job)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Salary scoring
# ---------------------------------------------------------------------------

class TestScoreSalary:

    def test_expected_within_range_gives_full_score(self):
        candidate = make_candidate([], 3, "NYC", 90000)
        job = make_job([], 2, "NYC", False, 80000, 120000)
        score, _ = score_salary(candidate, job)
        assert score == WEIGHT_SALARY

    def test_job_pays_more_than_expected_gives_full_score(self):
        candidate = make_candidate([], 3, "NYC", 70000)
        job = make_job([], 2, "NYC", False, 90000, 130000)
        score, _ = score_salary(candidate, job)
        assert score == WEIGHT_SALARY

    def test_job_max_below_expectation_near_zero(self):
        candidate = make_candidate([], 3, "NYC", 120000)
        job = make_job([], 2, "NYC", False, 60000, 80000)
        score, _ = score_salary(candidate, job)
        assert score < WEIGHT_SALARY * 0.1

    def test_no_salary_overlap_scores_very_low(self):
        candidate = make_candidate([], 3, "NYC", 200000)
        job = make_job([], 2, "NYC", False, 50000, 60000)
        score, _ = score_salary(candidate, job)
        assert score < 1.0


# ---------------------------------------------------------------------------
# Full scorer — score_job_for_candidate
# ---------------------------------------------------------------------------

class TestScoreJobForCandidate:

    def test_missing_must_have_returns_none(self):
        candidate = make_candidate(["JavaScript"], 5, "NYC", 100000)
        job = make_job([{"skill": "Python", "type": "must-have"}], 3, "NYC", False, 90000, 130000)
        result = score_job_for_candidate(candidate, job)
        assert result is None

    def test_perfect_match_scores_100(self):
        candidate = make_candidate(["Python", "PostgreSQL"], 5, "NYC", 100000)
        job = make_job(
            [{"skill": "Python", "type": "must-have"}, {"skill": "PostgreSQL", "type": "must-have"}],
            5, "NYC", False, 90000, 130000
        )
        result = score_job_for_candidate(candidate, job)
        assert result is not None
        assert result["score"] == 100.0

    def test_result_has_breakdown(self):
        candidate = make_candidate(["Python"], 3, "NYC", 90000)
        job = make_job([{"skill": "Python", "type": "must-have"}], 3, "NYC", False, 80000, 120000)
        result = score_job_for_candidate(candidate, job)
        assert result is not None
        assert "breakdown" in result
        assert "skills" in result["breakdown"]
        assert "experience" in result["breakdown"]
        assert "location" in result["breakdown"]
        assert "salary" in result["breakdown"]


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------

class TestRankJobsForCandidate:

    def test_ranked_by_score_descending(self):
        candidate = make_candidate(["Python"], 5, "NYC", 100000)
        job_high = make_job([{"skill": "Python", "type": "must-have"}], 3, "NYC", False, 90000, 130000, id=1)
        job_low = make_job([{"skill": "Python", "type": "must-have"}], 3, "Chicago", False, 50000, 60000, id=2)
        ranked = rank_jobs_for_candidate(candidate, [job_high, job_low])
        assert ranked[0]["score"] >= ranked[1]["score"]

    def test_limit_is_respected(self):
        candidate = make_candidate(["Python"], 5, "NYC", 100000)
        jobs = [
            make_job([{"skill": "Python", "type": "must-have"}], 2, "NYC", False, 80000, 120000, id=i)
            for i in range(10)
        ]
        ranked = rank_jobs_for_candidate(candidate, jobs, limit=3)
        assert len(ranked) == 3

    def test_hard_filtered_jobs_excluded(self):
        candidate = make_candidate(["JavaScript"], 5, "NYC", 100000)
        job_python = make_job([{"skill": "Python", "type": "must-have"}], 2, "NYC", False, 80000, 120000, id=1)
        job_js = make_job([{"skill": "JavaScript", "type": "must-have"}], 2, "NYC", False, 80000, 120000, id=2)
        ranked = rank_jobs_for_candidate(candidate, [job_python, job_js])
        assert len(ranked) == 1
        assert ranked[0]["job_id"] == 2
