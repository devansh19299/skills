---
name: retro
description: Write a short retrospective after completing a task or session. Captures what went well, what was slow, and one improvement for CLAUDE.md. Run after any non-trivial task.
---

Write a retrospective for this task/session. Keep it short — this is for your own improvement, not documentation.

Save to `docs/retros/YYYY-MM-DD-<topic>.md` (create `docs/retros/` if it doesn't exist).

## Format

```markdown
# Retro — <topic> — <date>

## What was done
- [one line per completed item]

## What went well
- [specific things that worked — tools, approaches, patterns]

## What was slow or painful
- [specific friction points — repeated searches, wrong assumptions, scope creep]

## One thing to add to CLAUDE.md
- [a rule, convention, or fact that would have saved time today]

## Token waste spotted
- [any repeated reads, unnecessary searches, or context bloat]
```

## After writing

1. If "One thing to add to CLAUDE.md" is non-trivial — add it to `/workspace/development/CLAUDE.md` now
2. Update `SESSION.md` with the retro file path under a "Retros" section
3. Say: "Retro written to docs/retros/YYYY-MM-DD-topic.md"
