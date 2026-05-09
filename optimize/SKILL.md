---
name: optimize
description: Use when improving performance, reducing token usage, fixing slow queries, or cutting context bloat. Defines metrics first, measures bottlenecks, applies macro fixes before micro.
arguments: [target]
---

Optimize: $target

## Step 1 — Define metrics first

Before changing anything, lock in what you're measuring:
- Token usage? Query time? Memory? Context window fill rate? Startup time?
- What's the current baseline (measure it now)?
- What's the target?

Do not optimize without a before/after measure.

## Step 2 — Find the real bottleneck

**Static analysis first (often faster than profiling):**
- Wrong algorithm or data structure?
- Unnecessary repeated work (re-reading same file, re-searching same corpus)?
- Work happening in the wrong layer?
- Asymptotic complexity obviously wrong?

**For token/context bloat specifically, check:**
```bash
# How full is the context window? (read from transcript)
python3 ~/.claude/skills/dev/context_watch.py

# What's eating the most tokens in corpus output?
python3 search_corpus.py "$target" --top 5 --compact  # compact vs full diff
```

**For query/API bottlenecks:**
```bash
# Find slow bench operations
tail -100 logs/frappe.log | grep -E "took [0-9]+" | sort -t' ' -k2 -rn | head -20

# Find N+1 query patterns  
bench --site <site> console  # frappe.db.sql('EXPLAIN ...')
```

## Step 3 — Macro before micro

Fix the largest category of waste first:
1. **Remove whole classes of work** — caching, deduplication, lazy loading
2. **Fix algorithms** — wrong complexity, wrong data structure
3. **Fix batching** — N+1 queries → single query, serial → parallel
4. **Then tune** — only after 1-3 are done

For token savings specifically, macro wins:
- Compact corpus scan instead of full scan (saves ~70% per result)
- Delta search instead of re-searching (skips already-seen records)
- SESSION.md to avoid re-explaining context (saves full re-discovery)
- Smaller `--top N` on corpus searches

## Step 4 — Apply and re-measure

Apply the highest-leverage fix first. Then re-measure against Step 1 baseline.
If target is met, stop. If not, repeat from Step 2 with the next bottleneck.

## Guardrails
- Never claim improvement without before/after numbers
- Don't optimize what you haven't measured
- Watch for regressions: correctness, reliability, security
- Prefer reversible changes
