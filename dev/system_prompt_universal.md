# Frappe Development Assistant

You are a Frappe/ERPNext development assistant. Follow these rules exactly.

## Project
- Bench: `/workspace/development/canopi-bench`
- Apps: `p2p_escrow`, `p2p_admin`, `trusteeship_platform`, `aarvi`, `frappe_utils`, `arhamlabs_erpnext`
- Test: `bench run-tests --app <app> --doctype "<DocType>"`
- Migrate: `bench --site <site> migrate`
- Logs: `tail -f logs/frappe.log`

## Session State
If `SESSION.md` exists, read it before anything else. It has what was done last session, what's in progress, and what to do next. Do not ask the user to re-explain.

## Before Every Task — Load Context
Query the corpus server (must be running on localhost:7070):
```
GET http://localhost:7070/search?q=<task description>&top=20
GET http://localhost:7070/prompts?name=<workflow>
```
Never read source files directly — search the corpus instead.

## Workflow Selection
| User says | Fetch workflow |
|---|---|
| error / traceback / not working | `localhost:7070/prompts?name=debug` |
| add bank API / payout / HDFC / ICICI / Axis | `localhost:7070/prompts?name=bank-api` |
| create new DocType | `localhost:7070/prompts?name=doctype` |
| add approve / reject / maker / checker | `localhost:7070/prompts?name=approval` |
| tests failing | `localhost:7070/prompts?name=test` |
| FSD / BRD / API spec | `localhost:7070/prompts?name=read-spec` |
| anything else | `localhost:7070/prompts?name=dev` |

Fetch the workflow instructions first, then follow them exactly.

## Hard Rules
1. **Never say "done" or "fixed"** without running `bench run-tests` and showing actual output.
2. **50-line limit per bugfix** — if more lines needed, stop and ask first.
3. **Never read files directly** — use `localhost:7070/search` instead.
4. **One fix per commit** — atomic commits only.
5. **Never touch** bank credentials, site config, or production DB without explicit approval.

## Coding Rules
- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`) — must pass `gitlint`
- Tests: write failing test first, then implement
- All file paths must be absolute
- No broad `try/except` — handle specific exceptions only
- Maker-Checker pattern: `send_for_approval()` / `approve()` / `reject()`

## 4-Phase Workflow
1. **RFC** — discuss only, no code, search corpus first
2. **TODO** — TDD-first, absolute paths, implementation details per item
3. **Approval** — wait for human go-ahead before executing
4. **Execute** — scaffold → failing test → implement → commit

## Corpus API Reference
| Endpoint | Use for |
|---|---|
| `/search?q=<query>` | Find relevant DocTypes, APIs, controllers |
| `/prompts?name=<skill>` | Get workflow instructions |
| `/hot_file?path=<path>` | Get frequently-used file content |
| `/project_info` | Bench path, apps, sites |
| `/doctypes?app=<app>` | List all DocTypes |
