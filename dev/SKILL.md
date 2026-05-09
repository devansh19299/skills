---
name: dev
description: Start a development task using the 4-phase workflow (RFC → TODO → Human approval → TDD execution). Automatically loads relevant corpus context. Use for any Frappe or general development task.
arguments: [task]
---

You are starting a development task. Follow the 4-phase workflow strictly.

## Step 1 — Load Corpus Context (phased to save tokens)

**Phase A — compact broad scan (cheap):** identify which records are relevant.
```bash
python3 search_corpus.py "$task" --top 15 --compact
```
Or via MCP: `search_corpus_compact(query="$task", top=15)`

Read the one-liners. Pick the 3-5 most relevant names.

**Phase B — full detail on top hits only:**
```bash
python3 search_corpus.py "<specific DocType or controller name>" --top 5
```
Or via MCP: `search_corpus(query="<specific name>", top=5)`

For follow-up searches (if Phase B raises new questions), use delta to skip already-seen records:
```bash
# MCP only:
search_corpus_delta(query="<new angle>", top=5)
```

If no corpus tools exist, ask: "Should I generate a corpus.jsonl for this project first?"

## Step 2 — Phase 1: RFC (Discuss Only)

Using only the corpus output above (no additional file reads), produce a Markdown RFC:
- What needs to be built and why
- Which existing DocTypes/APIs are involved (name them from corpus output)
- Architectural boundaries — what should NOT change
- Open questions for the human

**Rule: No code. No file creation. Discussion only.**

## Step 3 — Phase 2: Granular TODO

Transform the RFC into a hyper-specific TODO list. Every item must:

- **TDD First**: test item before implementation item
- **Absolute paths**: every file uses its full workspace path
- **Implementation block**: describe expected logic per item
- **Test command**: include the exact bench run-tests command

Format:
```
- [ ] TEST: <what it verifies> — `bench run-tests --app <app> --doctype "<DocType>"`
      File: /full/path/to/test_file.py
      Logic: <what the test asserts>

- [ ] IMPL: <what to implement>
      File: /full/path/to/controller.py
      Logic: <exact implementation detail>
```

## Step 4 — Phase 3: Human Gatekeeping

Present the TODO list and ask:
> "Does this TODO match what you want? Any changes before I start executing?"

**Do not proceed until the user approves.**

## Step 5 — Phase 4: Execute

Work through the TODO list one item at a time:
1. Scaffold with `bench` CLI if new DocType
2. Write the failing test — run it to confirm it fails
3. Implement until `bench run-tests` passes
4. Commit with a Conventional Commit message

For any additional context needed mid-execution, use `search_corpus_delta` (MCP) to avoid re-sending already-loaded context.

After each file edit, the corpus auto-updates via the PostToolUse hook.
