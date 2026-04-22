from job_hunter.apply.naukri_apply import _build_profile_context
from job_hunter.resume.schema import ResumeProfile


def test_build_profile_context_includes_detailed_profile() -> None:
    profile = ResumeProfile(
        name="Test User",
        total_experience_years=6,
        skills=["Python", "Node.js"],
        tech_stack=["Node.js"],
        past_roles=["Backend Engineer"],
    )
    detailed_profile = {
        "tech_experience": {"Node.js": 5, "AWS": 2},
        "achievements": ["Shipped a microservices migration"],
        "key_responsibilities": ["API design", "Team leadership"],
    }

    context = _build_profile_context(profile, detailed_profile)

    assert "Node.js: 5 years" in context
    assert "AWS: 2 years" in context
    assert "supplemental context only" in context
    assert "Backend Engineer" in context
