from job_hunter.apply.naukri_apply import _build_job_context


def test_build_job_context_includes_all_fields() -> None:
    job = {
        "title": "Senior QA Engineer",
        "company": "Acme Corp",
        "experience_required": "4-7 Yrs",
        "location": "Bengaluru",
        "work_mode": "hybrid",
        "salary_lpa": "20-30 LPA",
        "required_skills": ["Java", "Selenium", "TestNG"],
        "description": "We need a QA engineer to build automation frameworks.",
    }
    context = _build_job_context(job)

    assert "Senior QA Engineer" in context
    assert "Acme Corp" in context
    assert "Java, Selenium, TestNG" in context
    assert "automation frameworks" in context


def test_build_job_context_handles_none() -> None:
    assert _build_job_context(None) == "Not available"


def test_build_job_context_handles_partial_job() -> None:
    job = {"title": "QA Engineer"}
    context = _build_job_context(job)
    assert "QA Engineer" in context
    assert "Company:" not in context
