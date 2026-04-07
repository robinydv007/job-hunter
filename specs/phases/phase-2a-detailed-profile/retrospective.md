# Phase 2a — Retrospective

**Completed**: 2026-04-07  
**Release**: v0.2.0 (planned)

---

## What Went Well

- **Single LLM call design**: Extracting both basic + detailed profile in one call was efficient and reduced API costs
- **Hash-based cache detection**: SHA256-based resume change detection works reliably
- **Config split**: Separating screening.yaml from user.yaml keeps configs clean and manageable
- **Testing during development**: Fixed issues early (None values in LLM response, config loading)

---

## What Didn't Go Well

- **Initial cache issue**: The --force-parse flag wasn't properly passed through to the parser, requiring a fix after initial implementation
- **YAML null values**: User config had `null` values for some fields causing Pydantic validation errors - had to fix config files manually
- **Missing Rich Confirm import**: Clean command had unnecessary import that failed

---

## Lessons Learned

1. **Always test with fresh cache**: When implementing cache-busting features, test with actual cache files present
2. **Pydantic defaults matter**: Use proper Field defaults for optional fields to handle YAML null values
3. **Keep CLI simple**: Don't import unused modules, especially from Rich which may not have all submodules

---

## Deliverables Completed

| Deliverable | Status |
|-------------|--------|
| config/screening.yaml | ✅ Created |
| Single LLM extraction | ✅ Implemented |
| data/profile_detailed.yaml | ✅ Auto-generated |
| Config loading (both files) | ✅ Working |
| Resume change detection | ✅ Working (SHA256 hash) |
| --force-parse fix | ✅ Fixed |

---

## Next Steps

Phase 2b: Auto-Apply & Batch Screening
- Auto-apply to jobs above threshold
- Batch screening: scrape all questions, single LLM call
- Enhanced CSV tracking with apply status