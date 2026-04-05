# Project Charter

## Problem Statement
Job hunting on Indian job platforms requires extensive manual effort to search for listings, evaluate their relevance against a resume, and track application statuses. Candidates lack an automated way to filter the noise and find suitable jobs without spending hours manually searching.

## Goals
1. Build an agentic AI system that reads a user's resume and extracts a structured profile.
2. Autonomously discover relevant jobs based on candidate profiles and configuration settings.
3. Evaluate and score each job on a 0-100 scale using a transparent weighted rubric.
4. Maintain a single source of truth structured CSV containing match scores, reasons for selection, and status updates.
5. (Phase 2) Automatically apply to jobs that exceed an apply threshold, answering screening questions dynamically.

## Non-Goals (MVP phase)
* Auto-apply (moved to Phase 2)
* Multi-platform search beyond Naukri (moved to Phase 2)
* Company intelligence enrichment (moved to Phase 2)
* Resume tailoring or editing per job
* Email or notification alerts
* Custom Dashboard or web UI (using CSV tracking instead)

## Stakeholders
| Role | Name/Team |
|------|-----------|
| Owner | User / Job Hunter |
