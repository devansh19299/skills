# Complete Frappe AI Development Setup Guide

Everything we built from scratch — what it is, why it exists, and how to use it.

---

## The Problem We Solved

Every Claude session started from zero:
- Re-explain the codebase every time (~800 tokens wasted)
- Claude re-reads the same 15 files every session (~456 wasted reads)
- No workflow discipline — scope creep, hallucinated "done", no tests first
- Skills locked to Claude Code only — Codex/Antigravity/Gemini got nothing

**What we built:** A portable AI development harness that works across Claude Code, Codex, Antigravity, and Gemini — with corpus context, session continuity, auto-updating knowledge, and structured workflows.

---

## 1. Corpus (`corpus.jsonl`)

**What:** A structured, machine-readable knowledge dump of your entire Frappe codebase. 1,782 records covering every DocType schema, controller method, whitelisted API, hook, and frequently-used file.

**Why:** Instead of Claude re-reading `bank_adapter.py` (153 times across sessions), it searches the corpus and gets exactly what it needs in <100 tokens.

**Generate:**
```bash
cd /workspace/development
python3 generate_corpus.py
# Output: corpus.jsonl (1,782 records, 1.9MB)
```

**What's inside:**
```jsonl
{"type": "doctype", "name": "Batch File", "app": "p2p_escrow", "fields": [...]}
{"type": "controller", "controller": "BatchFile", "methods": ["validate", "send_for_approval", ...]}
{"type": "api", "function": "get_approval_batches", "args": ["page", "page_size"], ...}
{"type": "hot_file", "path": "apps/p2p_escrow/p2p_escrow/bank_adapter.py", "content": "...full file..."}
```

**Filter by app or type:**
```bash
python3 generate_corpus.py --apps p2p_escrow p2p_admin
```

---

## 2. Corpus Search (`search_corpus.py`)

**What:** Searches `corpus.jsonl` and returns only relevant records for a task. Replaces reading 20+ files with a targeted query returning <20 records.

**Why:** The full corpus is 375k tokens — way too large to read. Search returns ~2k tokens of exactly what's needed.

**Example:**
```bash
python3 search_corpus.py "batch file approval maker checker" --top 10

# Output:
# [doctype] Batch File — app:p2p_escrow
#   status (Select) → Draft / Pending Approval / Approved / Rejected
#   maker_user (Link) → User
#   checker_user (Link) → User
#
# [api] send_for_approval_api(file_name) — apps/p2p_escrow/...
# [api] approve_file_api(file_name, remarks) — apps/p2p_escrow/...
# [controller] BatchFile — def send_for_approval() / def approve_file() / ...
```

**Filter by app or type:**
```bash
python3 search_corpus.py "payout" --app p2p_escrow --type api --top 5
```

---

## 3. Corpus Server (`corpus_server.py`)

**What:** A server that exposes the corpus as MCP tools (for Claude Code, Codex, Antigravity) and as HTTP endpoints (for Gemini and any other tool).

**Start HTTP mode (for Gemini/curl):**
```bash
python3 corpus_server.py --http
# Running on http://localhost:7070
```

**Start MCP mode (auto — Claude Code uses this via .mcp.json):**
```bash
python3 corpus_server.py
```

**HTTP endpoints:**
```bash
# Search codebase
curl "localhost:7070/search?q=payout+approval&top=10"

# Get system prompt for Codex/Antigravity
curl "localhost:7070/system-prompt"

# Get workflow instructions
curl "localhost:7070/prompts?name=bank-api"

# List all skills
curl "localhost:7070/prompts"

# Get a hot file
curl "localhost:7070/hot_file?path=apps/p2p_escrow/p2p_escrow/bank_adapter.py"

# List all DocTypes
curl "localhost:7070/doctypes?app=p2p_escrow"

# Project info
curl "localhost:7070/project_info"
```

**MCP tools (Claude Code / Codex / Antigravity with MCP):**
```
search_corpus("payout approval", top=10)
get_hot_file("apps/p2p_escrow/p2p_escrow/bank_adapter.py")
list_doctypes(app="p2p_escrow")
list_prompts()
get_prompt("bank-api")
project_info()
```

---

## 4. Skills

Skills are reusable workflow instructions. Claude Code invokes them automatically based on what you describe. Other tools fetch them via HTTP.

### `/dev` — General Development (4-Phase Workflow)

**Trigger:** Any feature, task, or enhancement.

**Flow:**
```
1. RFC    → discuss only, search corpus, no code
2. TODO   → TDD-first, absolute paths, implementation blocks per item
3. Approval → wait for human go-ahead
4. Execute → scaffold → failing test → implement → commit
```

**Example:**
```
You: "add fee calculation to Batch File"

Claude:
Phase 1 — RFC:
  search_corpus("batch file fee calculation")
  → finds BatchFile controller, relevant fields
  → proposes: add fee_amount field, calculate in validate()

Phase 2 — TODO:
  - [ ] TEST: verify fee calculated correctly
        File: /workspace/development/canopi-bench/apps/p2p_escrow/.../test_batch_file.py
        Logic: create doc with amount=1000, assert fee_amount==20
  - [ ] IMPL: add fee_amount field to batch_file.json
  - [ ] IMPL: add _calculate_fee() to BatchFile controller

Phase 3: "Does this TODO match what you want?"

Phase 4: Execute step by step
```

---

### `/debug` — Debug Frappe Errors

**Trigger:** traceback, error, something not working.

**Example:**
```
You: "ValidationError in batch file approval"

Claude:
1. tail -f logs/frappe.log | grep ValidationError
2. Identifies: line 284 in batch_file.py — amount is None
3. Traces: send_for_approval() called before amount set
4. Fix: add validation check before approval
5. Runs bench run-tests — shows output
```

---

### `/bank-api` — Bank API Integration

**Trigger:** add bank, new payout API, HDFC/ICICI/Axis.

**Example:**
```
You: "add HDFC transfer API"

Claude:
1. get_hot_file("bank_adapter.py") → loads existing adapter patterns
2. RFC: HDFC uses OAuth, JWE encryption, maps to internal Payout fields
3. TODO: test → payload builder → API call → response parser → status mapper
4. Every request logged to Escrow API Log
```

---

### `/doctype` — Create New DocType

**Trigger:** "create a DocType for..."

**Example:**
```
You: "create Escrow Fee Schedule DocType"

Claude:
1. search_corpus("fee schedule") → finds similar DocTypes
2. RFC: fields (fee_type, amount, currency, effective_date), submittable
3. bench new-doctype "Escrow Fee Schedule" --app p2p_escrow
4. Write failing test → implement validate() → tests pass
```

---

### `/approval` — Maker-Checker Workflow

**Trigger:** "add approve/reject to...", "maker checker"

**Standard pattern generated:**
```python
def send_for_approval(self):
    if self.status != "Draft":
        frappe.throw(_("Only Draft can be sent for approval"))
    self.status = "Pending Approval"
    self.maker_user = frappe.session.user
    self.save()

def approve(self, remarks=""):
    if self.maker_user == frappe.session.user:
        frappe.throw(_("Maker cannot approve own submission"))
    self.status = "Approved"
    self.checker_user = frappe.session.user
    self.save()
```

---

### `/test` — Run & Fix Tests

**Trigger:** "run tests", "tests failing"

**Example:**
```
You: "tests failing for Batch File"

Claude:
1. bench run-tests --app p2p_escrow --doctype "Batch File"
2. Shows: FAIL test_send_for_approval — AssertionError: 'Draft' != 'Pending Approval'
3. Root cause: status not saved after send_for_approval()
4. Fix: add self.save() → re-runs → green
```

---

### `/read-spec` — Parse FSD/BRD Docs

**Trigger:** share an API spec, FSD, or BRD document.

**Output format:**
```
API Endpoints:
  POST /api/transfer — Auth: OAuth Bearer
  GET  /api/status   — Auth: OAuth Bearer

Request Fields:
  amount       → payout.amount
  account_no   → payout.bank_account
  ifsc_code    → payout.ifsc_code

Status Codes:
  SUCCESS  → Payout.status = "Success"
  PENDING  → Payout.status = "Initiated"
  FAILED   → Payout.status = "Failed"
```

---

### `/handoff` — Session Continuity

**Trigger:** end of any work session.

**What it writes to `SESSION.md`:**
```markdown
# Session — 2026-05-03

## Done
- Fixed HDFC response parser (bank_adapter.py:312)
- Tests passing for success + timeout cases

## In Progress
- HDFC beneficiary registration API
  File: apps/p2p_escrow/p2p_escrow/bank_adapter.py:~400
  State: request payload built, response parser not started

## Blocked
- Need HDFC sandbox credentials from Prabal

## Next Session — Start Here
1. Implement HdfcAdapter.parse_beneficiary_response()
2. Run bench run-tests --app p2p_escrow
3. Push to UAT after tests pass
```

**Next session:** Claude reads `SESSION.md` automatically — no re-explaining needed.

---

### `/retro` — Retrospective

**Trigger:** after completing any non-trivial task.

**Output saved to `docs/retros/2026-05-03-hdfc-api.md`:**
```markdown
# Retro — HDFC API — 2026-05-03

## Done
- Transfer API, status polling, error handling

## What went well
- corpus search found existing ICICI pattern to follow — saved 2 hours

## What was slow
- Spent 45 min re-reading bank_adapter.py — already in corpus, should have searched first

## One thing to add to CLAUDE.md
- Always search corpus before reading any file in apps/

## Token waste spotted
- Read bank_adapter.py 3 times — now a hot file in corpus
```

---

## 5. Auto-Updates

### Corpus auto-refresh on file edit
Every time you edit a `.py` or `.json` file inside `canopi-bench/apps/`, the corpus regenerates automatically. No manual step.

```
You edit bank_adapter.py
     ↓
PostToolUse hook fires
     ↓
generate_corpus.py runs silently
     ↓
corpus.jsonl updated
     ↓
[corpus] Done. ← appears in terminal
```

### Daily hot file update (cron, 6am)
```bash
# Runs automatically every morning
bash /workspace/development/refresh_corpus_daily.sh

# What it does:
# 1. Analyses chat history → finds files read 5+ times
# 2. Updates HOT_FILES in generate_corpus.py
# 3. Regenerates corpus.jsonl with fresh hot files
```

### Session auto-checkpoint (Stop hook)
When Claude Code session ends, `SESSION.md` is automatically checkpointed.

---

## 6. CLAUDE.md & .claudeignore

### CLAUDE.md
Loaded automatically every session. Contains environment, commands, corpus tools, hard rules, and workflow. Static content at top for Anthropic prompt cache hits.

**Hard rules enforced:**
- Cannot say "done" without running tests and showing output
- Max 50 lines per bugfix
- Subagents for file search (not main session)
- One fix per commit

### .claudeignore
Prevents Claude from reading files that waste tokens:
```
*.sql.gz        # database dumps
logs/           # use tail -f instead
*.xlsx *.docx   # binary files
node_modules/   # build artifacts
__pycache__/
```

---

## 7. GitHub Repo

Everything is in **github.com/devansh19299/skills**.

**Install in any new container:**
```bash
# Step 1 — install skill globally
curl -fsSL https://raw.githubusercontent.com/devansh19299/skills/main/dev/bootstrap_dev_skill.sh | bash

# Step 2 — set up in your project
cd /your/frappe/bench
bash ~/.claude/skills/dev/install.sh
# This: copies scripts, generates corpus.jsonl, sets up hooks, creates .mcp.json
```

**Skills in the repo:**
```
skills/
├── dev/           # /dev + all corpus tools + install scripts
├── debug/         # /debug
├── bank-api/      # /bank-api
├── doctype/       # /doctype
├── approval/      # /approval
├── test/          # /test
├── read-spec/     # /read-spec
├── handoff/       # /handoff
└── retro/         # /retro
```

---

## 8. Using With Other AI Tools

### Claude Code (automatic)
Just describe your task. Skills auto-invoke, corpus auto-searched, SESSION.md auto-read.

### Codex / Antigravity (with MCP)
Add to MCP config:
```json
{
  "mcpServers": {
    "corpus": {
      "type": "stdio",
      "command": "python3",
      "args": ["/workspace/development/corpus_server.py"]
    }
  }
}
```
Then the AI can call `search_corpus()`, `get_prompt()`, `get_hot_file()` directly.

### Gemini / Any tool (HTTP)
```bash
# Start server once
python3 corpus_server.py --http

# Get system prompt — paste into custom instructions
curl localhost:7070/system-prompt

# Before each task
curl "localhost:7070/prompts?name=bank-api"    # get workflow
curl "localhost:7070/search?q=HDFC+payout"    # get code context
```

---

## 9. Token Savings Summary

| What | Tokens saved per session |
|---|---|
| Corpus search vs re-reading files | ~5,000 tokens |
| Hot files embedded (no re-reads) | ~3,000 tokens |
| SESSION.md vs re-explaining | ~650 tokens |
| .claudeignore blocks | ~500 tokens |
| Subagents for search | ~1,000 tokens |
| **Total estimate** | **~10,000 tokens/session** |

---

## 10. File Map

```
/workspace/development/
├── CLAUDE.md                    ← auto-loaded every session
├── .claudeignore                ← files Claude never reads
├── .mcp.json                    ← wires corpus MCP to Claude Code
├── SESSION.md                   ← updated by /handoff each session
├── corpus.jsonl                 ← 1,782 records, auto-updated
├── corpus_server.py             ← MCP + HTTP server
├── generate_corpus.py           ← builds corpus.jsonl
├── search_corpus.py             ← searches corpus
├── analyse_chats.py             ← finds token waste in chat history
├── refresh_corpus_daily.sh      ← daily cron (6am)
├── system_prompt_universal.md   ← paste into Codex/Antigravity
└── .claude/
    ├── settings.json            ← PostToolUse + Stop hooks
    └── hooks/
        ├── refresh_corpus.sh    ← runs after every file edit
        └── auto_handoff.sh      ← runs when session ends
```

---

## Quick Reference

```bash
# Search codebase
python3 search_corpus.py "your task" --top 20

# Refresh corpus manually
python3 generate_corpus.py

# Analyse token waste in past sessions
python3 analyse_chats.py

# Start HTTP server for other AI tools
python3 corpus_server.py --http

# Run tests
cd canopi-bench && bench run-tests --app p2p_escrow --doctype "Batch File"

# At end of session
/handoff      ← writes SESSION.md

# After completing a task
/retro        ← writes docs/retros/YYYY-MM-DD-topic.md
```
