# Phase 2a — Overview: Detailed Profile

**Status:** Planned  
**Target:** TBD  
**Release:** v0.2.0 (planned)

---

## Goal

Implement enhanced user profile system with single LLM extraction for both basic and detailed profiles, and separate screening config file.

---

## Scope

1. **File Restructure** — Split config into 4 files: user.yaml, screening.yaml, profile.json, profile_detailed.yaml
2. **Single LLM Extraction** — Extract both basic + detailed profile in ONE call
3. **Profile Detailed** — Auto-generated from resume, user-editable for extended context
4. **Screening Config** — Moved to separate file for better organization

---

## Why This Matters

Phase 1 produces a basic profile from resume. Phase 2a enhances this with:
- Extended profile data (tech experience, achievements, interests) stored alongside basic profile
- Detailed profile is available to pass alongside basic profile wherever profile data is sent to LLM
- Separate screening config for cleaner organization
- User-editable detailed profile for custom Q&A responses

This data is available for any future LLM operation — not changing current logic, just providing richer context.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Phase 2a Architecture                            │
└─────────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐     ┌─────────────────┐
     │  load_config    │ ──▶ │ parse_resume    │
     │    Node         │     │    Node         │
     └─────────────────┘     └─────────────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────┐
                     │   Single LLM Call              │
                     │   (basic + detailed)           │
                     └────────────────────────────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────┐
                     │  Save both profiles            │
                     │  - data/profile.json           │
                     │  - data/profile_detailed.yaml  │
                     └────────────────────────────────┘
```

---

## File Structure (4 files only)

| File | Contents | Source |
|------|----------|--------|
| `config/user.yaml` | profile, search, naukri, scoring, auto_apply | User config |
| `config/screening.yaml` | screening_answers (moved from user.yaml) | User config |
| `data/profile.json` | Basic parsed resume: name, email, phone, skills, etc. | LLM extracted |
| `data/profile_detailed.yaml` | Extended profile: tech_experience, achievements, interests | LLM extracted + user-editable |

---

## Migration: user.yaml → screening.yaml

Current `user.yaml` has `screening_answers` section. Move to separate `screening.yaml`:

```yaml
# config/screening.yaml
screening_answers:
  willing_to_relocate: true
  comfortable_with_shifts: false
  current_ctc_lpa: 22
  expected_ctc_lpa: 30
  notice_period: immediate joiner
  reason_for_change: Looking for better growth opportunities and challenging role
  visa_status: not applicable
  remote_work_preference: flexible
  current_employer: ""
  current_designation: ""
  years_in_current_role: 0
  highest_qualification: ""
  university_name: ""
  passing_year: 0
  gaps_in_employment: ""
  work_authorization: ""
  background_check_consent: true
  references_available: true

# Extended answers - user can add custom responses
screening_answers_extended:
  reason_for_change: |
    Looking for a role that offers greater technical challenges
    and leadership opportunities...
  strengths: |
    Strong problem-solving, quick learner, good communication...
  weaknesses: |
    Sometimes take on too many tasks at once...
  what_can_you_bring: |
    9 years full-stack experience, proven leadership...
```

---

## Single LLM Call for Resume Extraction

**Current (Phase 1)**: Two separate LLM calls (not implemented yet)
1. Extract basic profile → `profile.json`
2. Extract detailed profile → `profile_detailed.yaml`

**Phase 2a (New)**: ONE LLM call returns both

```python
async def parse_resume_full(resume_path: str) -> tuple[ResumeProfile, dict]:
    """Extract both basic and detailed profile in single LLM call."""
    
    resume_text = extract_text_from_file(resume_path)
    
    prompt = f"""You are a resume parser. Extract ALL information from this resume.

Return a JSON object with TWO sections: "basic" and "detailed".

BASIC SECTION (for profile.json):
- name, email, phone
- skills: list of technical skills
- tech_stack: list of technologies
- total_experience_years: number
- past_roles: list of role titles
- industry_domain: string
- location_preference: string
- salary_expectation: string if found
- target_roles: list of job titles you're targeting
- education: list of qualifications
- summary: 2-3 sentence professional summary

DETAILED SECTION (for profile_detailed.yaml):
- tech_experience: dict mapping technology to years of experience
  Example: {{"Python": 5, "AWS": 2, "React": 3}}
- achievements: list of 3-5 notable achievements
- challenges_solved: list of technical challenges overcome
- interests: list of professional interests
- extracted_summary: 2-3 sentence professional summary (can be same as basic.summary)
- key_responsibilities: list of main responsibilities from past roles

Resume text:
{resume_text}

Output as valid JSON with keys "basic" and "detailed":"""
    
    result = llm.generate_json(prompt)
    basic_profile = ResumeProfile(**result["basic"])
    detailed_profile = result["detailed"]
    
    return basic_profile, detailed_profile
```

---

## profile_detailed.yaml Structure

```yaml
# data/profile_detailed.yaml
# Auto-generated from resume (single LLM call) + user can edit

tech_experience:
  Python: 5
  JavaScript: 3
  React: 2
  AWS: 2
  Docker: 2
  Kubernetes: 1

achievements:
  - "Led team of 5 developers, delivered 3 major products"
  - "Received 'Best Innovator' award for AI automation tool"

challenges_solved:
  - "Scaled monolithic app to microservices reducing latency by 40%"
  - "Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 mins"

interests:
  - "Machine Learning"
  - "System Design"
  - "Open Source"

key_responsibilities:
  - "Architected scalable microservices using Python and Kubernetes"
  - "Led team of 5 junior developers"
  - "Implemented AI-based automation reducing manual work by 60%"

extracted_summary: |
  Experienced software engineer with 9 years in full-stack development...
  
# User can add custom Q&A for common questions
role_questions:
  - question: "Why should we hire you?"
    answer: "..."
  - question: "Where do you see yourself in 5 years?"
    answer: "..."

# User can add overrides
user_overrides:
  reason_for_change: |
    (User's custom reason if they want to override auto-generated)
```

---

## Config Updates

### user.yaml (profile, search, naukri, scoring, auto_apply)

```yaml
profile:
  name: Robin Yadav
  total_experience: 9
  preferred_roles:
  - Technical Lead
  - Senior Software Engineer
  resume_path: "resume.pdf"  # NEW: default is resume.pdf in project root
  # ... other profile fields

search:
  # ... (unchanged)

naukri:
  # ... (unchanged)

scoring:
  # ... (unchanged)

auto_apply:
  enabled: false  # Default: false
  require_confirmation: true
  skip_if_already_applied: true
```

### screening.yaml (new file)

```yaml
screening_answers:
  willing_to_relocate: true
  current_ctc_lpa: 22
  expected_ctc_lpa: 30
  notice_period: immediate joiner
  reason_for_change: Looking for better growth...
  # ... all other screening fields

screening_answers_extended:
  # User can add extended answers here
  # Or edit in profile_detailed.yaml
```

---

## Deliverables

| Deliverable | File(s) | Description |
|-------------|---------|-------------|
| screening.yaml | `config/screening.yaml` | Move screening_answers from user.yaml |
| Single LLM extraction | `resume/parser.py` | Extract basic + detailed in one call |
| profile_detailed.yaml | `data/profile_detailed.yaml` | Auto-created, user-editable |
| Config loading | `config/__init__.py` | Load both user.yaml and screening.yaml |
| Resume change detection | `resume/parser.py` | Regenerate if resume changes |

---

## Acceptance Criteria

- [ ] `screening.yaml` created and loaded correctly
- [ ] Resume parsing extracts basic + detailed in ONE LLM call
- [ ] `profile_detailed.yaml` created with all fields
- [ ] User can edit `profile_detailed.yaml` and changes persist
- [ ] Resume change detection regenerates both profiles
- [ ] Subsequent runs use cached profiles without LLM call

---

## Exit Criteria

- Single LLM call produces both `profile.json` and `profile_detailed.yaml`
- Both files load correctly in subsequent runs
- Resume change triggers regeneration
- All Phase 1 functionality continues to work

---

## Known Risks

| Risk | Mitigation |
|------|------------|
| LLM returns malformed JSON | Pydantic validation + fallback to error message |
| User edits break YAML | Load with safe loader, validate before save |
| Resume format variation | Handle PDF, DOCX, TXT; show clear error for unsupported |

---

## File Structure

```
config/
├── user.yaml           # profile, search, naukri, scoring, auto_apply
└── screening.yaml     # screening_answers (NEW - moved from user.yaml)

data/
├── profile.json        # Basic profile (already exists)
└── profile_detailed.yaml  # Extended profile (NEW - auto-generated)

src/job_hunter/
├── resume/
│   └── parser.py       # MODIFY: single LLM call for both profiles
└── config/
    └── __init__.py     # MODIFY: load screening.yaml, add resume_path
```

---

## Data Flow: Profile + Detailed Profile

**Current (Phase 1)**: Only basic `profile.json` sent to LLM for any operations.

**Phase 2a+**: Both `profile.json` AND `profile_detailed.yaml` available — passed together wherever profile data is sent to LLM.

This means any future LLM operation (scoring, screening answers, etc.) has access to:
- Basic profile: name, skills, experience, roles
- Detailed profile: tech_experience years, achievements, challenges, interests

Example usage in code:
```python
profile = load_profile()  # ResumeProfile
detailed = load_detailed_profile()  # dict

# Both passed together for richer LLM context
llm_context = {
    "profile": profile.model_dump(),
    "detailed": detailed
}
```

This does NOT change current scoring logic — just makes the data available.

---

## Next Steps (Phase 2b)

Once Phase 2a is complete:
- Auto-apply to Naukri jobs
- Batch screening: scrape all questions, single LLM call for all answers
- Enhanced CSV tracking with apply status