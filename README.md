# Claude Skills

Reusable Claude Code skills for development workflows.

## `/dev` — 4-Phase Development Workflow

Starts any development task using a structured RFC → TODO → Approval → TDD execution workflow. Automatically searches a `corpus.jsonl` of your codebase so Claude codes in *your* patterns, not generic ones.

### Install in any container or machine

```bash
curl -fsSL https://raw.githubusercontent.com/devansh19299/claude-skills/main/dev/bootstrap_dev_skill.sh | bash
```

### Set up corpus in a project

```bash
cd /your/frappe/project
bash ~/.claude/skills/dev/install.sh
```

### Usage

```
/dev add fee calculation to Batch File approval
```

Claude will:
1. Search the corpus for relevant DocTypes, controllers, and APIs
2. Present an RFC (no code yet)
3. Generate a granular TDD-first TODO list
4. Wait for your approval
5. Execute step by step

### What's included

| File | Purpose |
|---|---|
| `SKILL.md` | The `/dev` Claude Code skill |
| `generate_corpus.py` | Builds `corpus.jsonl` from your Frappe apps |
| `search_corpus.py` | Searches corpus for relevant context |
| `install.sh` | Sets up a project (corpus + auto-update hook) |
| `bootstrap_dev_skill.sh` | One-liner to install skill globally |
