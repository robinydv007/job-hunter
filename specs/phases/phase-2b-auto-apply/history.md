# Phase 2b — History: Auto-Apply

> Phase started: 2026-04-07  
> Status: NOT STARTED (replanning after implementation attempt)

---

[EXPLORATION] 2026-04-07 — Naukri Apply Flow Exploration
Topics: naukri, exploration, selectors, sidebar-form
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/phases/phase-2b-auto-apply/overview.md, specs/phases/phase-2b-auto-apply/plan.md
Detail: Created Playwright exploration script to understand actual Naukri apply flow. Discovered `.apply-button` selector triggers a sidebar form (not modal/page). Logged-in users see pre-filled fields including resume upload (input[type="file"]), experience dropdown (#experienceDD), and location input. Updated overview.md with actual selectors and implementation notes.

[IMPLEMENTATION] 2026-04-08 — Implementation Attempt (Subsequently Removed)
Topics: naukri, apply, state-machine, contenteditable, selectors
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/phases/phase-2b-auto-apply/tasks.md
Detail: Attempted implementation with state machine approach. Created apply/ package with analyzer.py, actions.py, storage.py, naukri_apply.py. Discovered critical issues that required significant rework - see challenges below. Code was subsequently removed to revert to clean state for replanning.

[CHALLENGES] 2026-04-08 — Key Challenges Discovered During Implementation
Topics: naukri, challenges, contenteditable, sequential-forms, search-blocking
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/phases/phase-2b-auto-apply/overview.md, specs/phases/phase-2b-auto-apply/plan.md
Detail: 
1. Naukri Search Blocking: Direct URL navigation returns "Access Denied" or empty page after login. Currently returns 0 jobs.
2. Contenteditable Divs: Naukri uses `contenteditable="true"` divs instead of `<input>` elements - required different filling approach.
3. Sequential Question Flow: Original plan was "batch all questions first → single LLM call → fill all". Naukri shows questions ONE AT A TIME in sidebar, requiring read-analyze-act loop instead.
4. Select/Option Fields: Notice Period dropdown uses clickable divs/radio buttons, not standard `<select>` elements.
5. Sidebar State Detection: Hard to detect when application was successfully submitted vs still in progress.
6. Submit Button Blocking: Chatbot overlay sometimes blocks submit button clicks.
7. Resume Upload Failure: Naukri often fails to upload resume - need "I'll do it later" skip option.

[DOC_FIX] 2026-04-09 — Fix Tasks Prerequisites Duplicates
Topics: docs, tasks, prerequisites
Affects-phases: phase-2b-auto-apply
Affects-docs: specs/phases/phase-2b-auto-apply/tasks.md
Detail: Removed duplicate prerequisite entries in tasks.md. All Phase 2a prerequisites are now correctly marked as complete ([x]) including resume change detection, cached profiles, and load_profile_with_detailed().