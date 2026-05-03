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

## How It Works

```
You describe a task
        │
        ▼
Skill auto-selected (Claude Code)
OR get_prompt("skill") via MCP
OR curl localhost:7070/prompts?name=skill
        │
        ▼
Corpus searched for relevant DocTypes/APIs
(search_corpus MCP tool OR curl localhost:7070/search)
        │
        ▼
4-phase workflow: RFC → TODO → Approval → Execute
```

---

## Available Skills

### `/dev` — General Development (4-phase workflow)
**Use when:** any feature, enhancement, or task that doesn't fit a specific skill below.

**What it does:**
1. Searches corpus for relevant DocTypes, APIs, controllers
2. Produces an RFC (discuss only, no code)
3. Generates a granular TDD-first TODO list with absolute paths
4. Waits for human approval
5. Executes step by step: scaffold → failing test → implement → commit

---

### `/debug` — Debug Frappe Errors
**Use when:** traceback, unexpected behaviour, something not working.

**What it does:**
1. Reads `frappe.log` and `worker.log`
2. Classifies error type (ValidationError, DoesNotExist, PermissionError, etc.)
3. Traces to root cause in the controller
4. Fixes the root cause (no broad try/except)
5. Verifies with `bench run-tests`

---

### `/bank-api` — Bank API Integration
**Use when:** adding or fixing a bank payment API (Axis, ICICI, HDFC, Razorpay, etc.).

**What it does:**
1. Loads `bank_adapter.py` and `api.py` from corpus (no re-reading)
2. RFC: identifies encryption type, field mappings, adapter pattern to follow
3. TDD TODO: test → payload builder → API call → response parser → status mapper
4. Logs every request/response to `Escrow API Log`

---

### `/doctype` — Create New DocType
**Use when:** building a new Frappe DocType from scratch.

**What it does:**
1. Searches corpus for similar existing DocTypes
2. RFC: defines fields, permissions, controller hooks needed
3. Scaffolds with `bench new-doctype`
4. Writes failing test first, then implements controller logic

---

### `/approval` — Maker-Checker Workflow
**Use when:** adding approve/reject functionality to a DocType.

**What it does:**
1. Adds status flow: Draft → Pending Approval → Approved / Rejected
2. Adds fields: maker_user, checker_user, datetime stamps, remarks
3. Implements `send_for_approval()`, `approve()`, `reject()` methods
4. Enforces: maker cannot approve own submission, checker role required

---

### `/test` — Run & Fix Tests
**Use when:** running bench tests or tests are failing.

**What it does:**
1. Runs `bench run-tests` and parses output
2. For each failure: shows test name, assertion, expected vs actual
3. Classifies root cause (wrong impl, wrong test, missing data, DB state)
4. Fixes and re-runs until all pass

---

### `/read-spec` — Parse FSD/BRD/API Spec
**Use when:** given a bank API spec, FSD, or BRD document to implement.

**What it does:**
1. Extracts endpoints, request/response fields, status codes
2. Identifies auth/encryption type
3. Maps spec fields → internal Frappe fields
4. Outputs an RFC ready for `/bank-api` or `/dev`

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
list_prompts()              → see all skills
get_prompt("debug")         → get skill instructions
search_corpus("payout")     → get relevant code context
project_info()              → bench path, apps, sites
```

### Tools without MCP (Gemini extension, etc.)
Start HTTP server once:
```bash
python3 corpus_server.py --http
# Running on http://localhost:7070
```

Then query:
```bash
curl "localhost:7070/prompts"                    # list all skills
curl "localhost:7070/prompts?name=bank-api"      # get skill instructions
curl "localhost:7070/search?q=payout+approval"   # get corpus context
curl "localhost:7070/project_info"               # bench/app info
```
Paste the output into your AI tool's chat as context.

---

## Corpus Tools

| File | Purpose |
|---|---|
| `generate_corpus.py` | Builds `corpus.jsonl` from your Frappe apps (DocTypes, controllers, APIs, hooks, hot files) |
| `search_corpus.py` | Searches corpus for relevant context — use instead of re-reading files |
| `corpus_server.py` | MCP + HTTP server exposing corpus and skills to any AI tool |
| `install.sh` | Sets up a project (generates corpus, installs hook, creates `.mcp.json`) |
| `bootstrap_dev_skill.sh` | One-liner to install everything globally |
| `CLAUDE.md.template` | Copy to your project root — gives any AI always-on project context |

### Corpus auto-updates
After install, `corpus.jsonl` regenerates automatically whenever you edit a `.py` or `.json` file inside `canopi-bench/apps/` — no manual step needed.

### Manual regeneration
```bash
python3 generate_corpus.py                        # all apps
python3 generate_corpus.py --apps p2p_escrow      # specific app
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
| anything else | `dev` | `get_prompt("dev")` |
