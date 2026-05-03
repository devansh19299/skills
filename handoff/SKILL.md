---
name: handoff
description: Write a session summary to SESSION.md so the next session starts with full context. Run this at the end of every work session. Keeps summaries short to minimise token cost.
---

Write a handoff summary for the next session. Be concise — every line costs tokens next session.

## Step 1 — Summarise this session

Based on everything discussed and done in this conversation, write `SESSION.md` in the current working directory:

```markdown
# Session — {{DATE}}

## Done
- [one line per completed thing, include file path if relevant]

## In Progress
- [task name]
  File: [absolute path:line if known]
  State: [what works, what doesn't, where it broke]

## Blocked
- [what's blocked and why — who/what is needed to unblock]

## Next Session — Start Here
1. [most important next action, specific enough to act on immediately]
2. [second action]
3. [third action]

## Context
[1-3 lines of non-obvious context that would take time to re-discover]
```

## Step 2 — Rules for writing it

- **Done**: only things actually completed, not attempted
- **In Progress**: include exact file + line number if mid-implementation
- **Blocked**: only real blockers, not things just not done yet
- **Next Session**: specific enough to act on without reading anything else
- **Context**: things that aren't obvious from the code (decisions made, why something was done a certain way, pending responses from people)
- **Total length**: under 300 words — if it's longer, cut it

## Step 3 — Confirm

After writing, show the contents and say:
> "SESSION.md written. Next session will start with this context automatically."
