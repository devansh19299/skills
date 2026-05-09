# Skills

Reusable AI development skills for Frappe projects. Works with Claude Code (auto), Codex, Antigravity, Gemini, and any MCP-compatible tool.

## Quick Install

```bash
# Any container — one command
curl -fsSL https://raw.githubusercontent.com/devansh19299/skills/main/dev/bootstrap_dev_skill.sh | bash

# Set up corpus in your project
cd /your/frappe/bench
bash ~/.claude/skills/dev/install.sh
```

---

## How It Works — Full Flow

```
You describe a task
        │
        ▼
① Skill auto-selected
   Claude Code: matched by description → SKILL.md loaded
   Codex/MCP:  call get_prompt("skill-name")
   Gemini/HTTP: curl localhost:7070/prompts?name=skill-name
        │
        ▼
② Corpus searched — two phases to save tokens
   Phase A (cheap): search_corpus_compact("task") → one-liner per record
                    identify which DocTypes/controllers matter
   Phase B (deep):  search_corpus("specific name") → full detail, top 5 only
   Follow-ups:      search_corpus_delta("new angle") → skips already-seen records
        │
        ▼
③ 4-Phase Workflow executes
   RFC → TODO → Human Approval → Execute
        │
        ▼
④ Corpus auto-updates after every file edit (PostToolUse hook)
        │
        ▼
⑤ Context watch runs on every turn (UserPromptSubmit hook)
   [Context [========----] 65% — 130K/200K tokens, 8 turns | OK]
```

### Token saving mechanisms — layered

| Layer | What it does | Saving |
|---|---|---|
| Compact scan (Phase A) | One-liner per record vs full dump | ~70% per result |
| Delta search | Skips records already in conversation | Eliminates re-sends |
| `--budget N` flag | Stops output before context overflow | Caps runaway searches |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` | Built-in micro-compaction at 45% vs 80% | Auto-prunes tool results early |
| `skillListingBudgetFraction: 0.06` | Prevents skill descriptions truncating | All skills visible |
| SESSION.md | Carries state across sessions — no re-explaining | ~650 tokens/session |
| `.claudeignore` | Blocks binary files, logs, dumps | ~500 tokens/session |
| `context_watch.py` hook | Shows real token % on every turn | Visibility to act early |

---

## Available Skills

### `/dev` — General Development (4-phase workflow)
**Use when:** any feature, enhancement, or task.

**Flow:**
```
① Compact corpus scan — identify relevant names cheaply
② Full detail on top 3-5 hits only
③ RFC — discuss only, no code
④ TODO — TDD-first, absolute paths, implementation details per item
⑤ Human approval gate — explicit go-ahead required
⑥ Execute — scaffold → failing test → implement → commit
   (delta search for any new context needed mid-execution)
```

---

### `/debug` — Debug Frappe Errors
**Use when:** traceback, unexpected behaviour, something not working.

**Flow:**
1. Reads `frappe.log` and `worker.log`
2. Classifies error type (ValidationError, DoesNotExist, PermissionError, etc.)
3. Traces to root cause in the controller
4. Fixes root cause (no broad try/except)
5. Verifies with `bench run-tests`

---

### `/bank-api` — Bank API Integration
**Use when:** adding or fixing a bank payment API (Axis, ICICI, HDFC, Razorpay, etc.).

**Flow:**
1. Compact corpus search on `bank_adapter.py` + `api.py`
2. RFC: encryption type, field mappings, adapter pattern to follow
3. TDD TODO: test → payload builder → API call → response parser → status mapper
4. Logs every request/response to `Escrow API Log`

---

### `/doctype` — Create New DocType
**Use when:** building a new Frappe DocType from scratch.

**Flow:**
1. Compact corpus search for similar existing DocTypes
2. RFC: fields, permissions, controller hooks
3. `bench new-doctype` scaffold
4. Failing test first, then controller logic

---

### `/approval` — Maker-Checker Workflow
**Use when:** adding approve/reject functionality to a DocType.

**What it adds:**
- Status flow: Draft → Pending Approval → Approved / Rejected
- Fields: maker_user, checker_user, datetime stamps, remarks
- Methods: `send_for_approval()`, `approve()`, `reject()`
- Rule: maker cannot approve own submission, checker role required

---

### `/test` — Run & Fix Tests
**Use when:** running bench tests or tests are failing.

**Flow:**
1. Runs `bench run-tests` and parses output
2. For each failure: shows test name, assertion, expected vs actual
3. Classifies root cause (wrong impl, wrong test, missing data, DB state)
4. Fixes and re-runs until all pass

---

### `/read-spec` — Parse FSD/BRD/API Spec
**Use when:** given a bank API spec, FSD, or BRD document.

**Output:**
- Endpoints, request/response fields, status codes
- Auth/encryption type identified
- Spec fields → internal Frappe fields mapped
- RFC ready for `/bank-api` or `/dev`

---

### `/handoff` — Session Continuity
**Use when:** end of any work session.

**Writes `SESSION.md` with:** done, in-progress (file:line), blocked, next session start, non-obvious context. Under 300 words. Next session auto-reads it — no re-explaining.

---

### `/retro` — Retrospective
**Use when:** after completing any non-trivial task.

**Captures:** what was done, what went well, what was slow, one rule for CLAUDE.md, token waste spotted.

---

### `/optimize` — Performance & Token Optimization
**Use when:** something is slow, using too many tokens, or context is bloating.

**Flow:**
1. Define metrics first (tokens? query time? context %)
2. Measure the baseline now
3. Static analysis for algorithmic issues
4. Macro fixes first (caching, dedup, batching) before micro-tweaks
5. Re-measure against baseline

---

## Corpus Tools

| File | Purpose |
|---|---|
| `generate_corpus.py` | Builds `corpus.jsonl` from Frappe apps (DocTypes, controllers, APIs, hooks, hot files) |
| `search_corpus.py` | Searches corpus — use `--compact` for broad scans, `--budget` to cap output size |
| `corpus_server.py` | MCP + HTTP server with session-dedup tools (`search_corpus_compact`, `search_corpus_delta`, `reset_session_cache`) |
| `context_watch.py` | Reads actual API token counts from transcript, outputs context % bar — use as UserPromptSubmit hook |
| `install.sh` | Sets up a project (corpus, hooks, `.mcp.json`, settings with CLAUDE_AUTOCOMPACT_PCT_OVERRIDE) |
| `bootstrap_dev_skill.sh` | One-liner global install |
| `system_prompt_universal.md` | Paste into Codex/Antigravity/Gemini system prompt |
| `CLAUDE.md.template` | Copy to project root — always-on project context |

### New corpus search modes (token-saving)

```bash
# Broad scan — one-liner per record (~70% fewer tokens)
python3 search_corpus.py "payout approval" --compact

# Stop before exceeding ~4000 chars output
python3 search_corpus.py "settlement" --budget 4000

# Skip sources already returned in this session (deduplicate)
# MCP only:
search_corpus_delta(query="new angle", top=5)

# Check context window usage
python3 context_watch.py
# → [Context [========----] 65% — 130K/200K tokens, 8 turns | OK]
```

### MCP tools (Claude Code / Codex / Antigravity)

```
search_corpus("task", top=10)           → full detail
search_corpus_compact("task", top=15)   → one-liner per record
search_corpus_delta("task", top=5)      → skip already-seen sources
reset_session_cache()                   → clear dedup set for new task
get_hot_file("path/to/file.py")
list_doctypes(app="p2p_escrow")
list_prompts()
get_prompt("bank-api")
project_info()
```

### HTTP endpoints (Gemini / curl)

```bash
curl "localhost:7070/search?q=payout&compact=1"      # one-liner per record
curl "localhost:7070/search?q=settlement&delta=1"    # skip seen sources
curl "localhost:7070/search?q=approval&top=5"        # full detail
curl "localhost:7070/prompts?name=debug"
curl "localhost:7070/system-prompt"
curl "localhost:7070/project_info"
```

### Corpus auto-updates

After install, `corpus.jsonl` regenerates automatically whenever you edit a `.py` or `.json` file inside `apps/` — no manual step needed.

```bash
# Manual regeneration
python3 generate_corpus.py                       # all apps
python3 generate_corpus.py --apps p2p_escrow     # specific app
```

---

## Settings (auto-configured by install.sh)

`install.sh` now writes these into `.claude/settings.json`:

```json
{
  "skillListingBudgetFraction": 0.06,
  "env": {
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"
  },
  "hooks": {
    "PostToolUse": [{ "matcher": "Edit|Write", ... }],
    "UserPromptSubmit": [{ "command": "python3 context_watch.py --hook" }]
  }
}
```

- **`skillListingBudgetFraction: 0.06`** — prevents skill descriptions from being truncated (Claude Code defaults to 1% which cuts off when many skills are installed)
- **`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 50`** — Claude Code's built-in micro-compaction activates at ~45% context instead of ~80%, keeping context lean automatically
- **`context_watch.py` hook** — injects a real token-usage bar into every turn so you can act before context fills

---

## Using With Other AI Tools

### Claude Code (automatic)
Skills are auto-invoked. Just describe the task in plain English.

### Tools with MCP support (Codex, Antigravity, Cursor, Windsurf)
Add to their MCP config:
```json
{
  "mcpServers": {
    "corpus": {
      "type": "stdio",
      "command": "python3",
      "args": ["/your/project/corpus_server.py"]
    }
  }
}
```
Then call:
```
list_prompts()                     → see all skills
get_prompt("debug")                → get skill instructions
search_corpus_compact("payout")    → cheap broad scan
search_corpus_delta("approval")    → follow-up without re-sending context
project_info()                     → bench path, apps, sites
```

### Tools without MCP (Gemini extension, etc.)
Start HTTP server once:
```bash
python3 corpus_server.py --http
# Running on http://localhost:7070
```

Then query:
```bash
curl "localhost:7070/prompts"                          # list all skills
curl "localhost:7070/prompts?name=bank-api"            # get skill instructions
curl "localhost:7070/search?q=payout+approval&compact=1"  # cheap broad scan
curl "localhost:7070/search?q=settlement&delta=1"      # skip already-seen
curl "localhost:7070/project_info"                     # bench/app info
```

---

## Skill Auto-Selection Guide

| User says | Skill | MCP call |
|---|---|---|
| error / traceback / not working | `debug` | `get_prompt("debug")` |
| add bank / payout / HDFC / ICICI / Axis | `bank-api` | `get_prompt("bank-api")` |
| create new DocType | `doctype` | `get_prompt("doctype")` |
| add approve / reject / maker / checker | `approval` | `get_prompt("approval")` |
| tests failing / run tests | `test` | `get_prompt("test")` |
| FSD / BRD / API spec doc | `read-spec` | `get_prompt("read-spec")` |
| slow / too many tokens / context bloating | `optimize` | `get_prompt("optimize")` |
| end of session | `handoff` | `get_prompt("handoff")` |
| after completing task | `retro` | `get_prompt("retro")` |
| anything else | `dev` | `get_prompt("dev")` |
