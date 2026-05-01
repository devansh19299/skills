---
name: dev
description: Start a development task using the 4-phase workflow (RFC → TODO → Human approval → TDD execution). Automatically loads relevant corpus context. Use for any Frappe or general development task.
arguments: [task]
---

You are starting a development task. Follow the 4-phase workflow strictly.

## Step 1 — Load Corpus Context

Run the following to find and search the corpus:

```bash
# Auto-generate corpus if missing
if [ ! -f corpus.jsonl ]; then
  echo "corpus.jsonl not found — generating..."
  python3 generate_corpus.py 2>/dev/null || echo "No generate_corpus.py found, skipping."
fi

# Search for relevant context
python3 search_corpus.py "$task" --top 20 2>/dev/null || echo "No search_corpus.py found."
```

Read the output carefully. These are the actual DocTypes, controllers, and APIs relevant to this task.

If no corpus tools exist, ask the user: "Should I generate a corpus.jsonl for this project first?"

## Step 2 — Phase 1: RFC (Discuss Only)

Using the corpus context above, produce a Markdown RFC covering:
- What needs to be built and why
- Which existing DocTypes/APIs are involved (reference them by name from corpus output)
- Architectural boundaries — what should NOT change
- Open questions that need human input

**Rule: No code. No file creation. Discussion only.**

## Step 3 — Phase 2: Granular TODO

Transform the RFC into a hyper-specific TODO list. Every item must follow these rules:

- **TDD First**: test item comes before implementation item
- **Absolute paths**: every file referenced uses its full workspace path
- **Implementation block**: each item describes the expected logic in detail
- **bench run-tests command**: include the exact test command for each test item

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

Present the TODO list and explicitly ask:
> "Does this TODO match what you want? Any changes before I start executing?"

**Do not proceed to Phase 4 until the user approves.**

## Step 5 — Phase 4: Execute

Work through the TODO list one item at a time:
1. Scaffold with `bench` CLI if new DocType
2. Write the failing test — run it to confirm it fails
3. Implement until `bench run-tests` passes
4. Commit with a Conventional Commit message

After each file edit, the corpus auto-updates via the PostToolUse hook.
