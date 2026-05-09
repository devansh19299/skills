#!/usr/bin/env python3
"""
MCP Corpus Search Server
Exposes corpus.jsonl as queryable MCP tools for Claude Code, Codex, Antigravity, etc.
Also serves HTTP on :7070 for non-MCP tools (Gemini extension, curl).

Usage (stdio MCP — Claude Code):
    python3 corpus_server.py

Usage (HTTP — Gemini / curl / other):
    python3 corpus_server.py --http
    curl http://localhost:7070/search?q=payout+approval&top=10

Usage (test):
    python3 corpus_server.py --test

Token-saving features:
    search_corpus_compact   — one-liner per record (~70% fewer tokens)
    search_corpus_delta     — skips sources already returned this session (deduplication)
    reset_session_cache     — clear the dedup set
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# ── Corpus loading ────────────────────────────────────────────────────────────

def _find_corpus() -> Path:
    env = os.environ.get("CORPUS_PATH")
    if env:
        return Path(env)
    for p in [Path.cwd(), *Path.cwd().parents]:
        c = p / "corpus.jsonl"
        if c.exists():
            return c
    return Path.cwd() / "corpus.jsonl"

def _find_bench() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "apps").exists() and (p / "sites").exists():
            return p
    return Path("/workspace/development/canopi-bench")

CORPUS_PATH = _find_corpus()
BENCH_PATH  = _find_bench()

STOP_WORDS = {
    "a","an","the","and","or","for","to","in","on","of","add","create",
    "build","make","new","get","set","update","with","this","that","from",
    "into","is","it","be","as",
}

_corpus_cache: list[dict] | None = None

# Session-level deduplication: tracks source paths already returned this session.
# Prevents re-sending the same context in follow-up searches (saves tokens).
_session_seen: set[str] = set()

def load_corpus() -> list[dict]:
    global _corpus_cache
    if _corpus_cache is not None:
        return _corpus_cache
    if not CORPUS_PATH.exists():
        return []
    records = []
    with CORPUS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    _corpus_cache = records
    return records


# ── Search logic ──────────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

def record_text(r: dict) -> str:
    parts = [
        r.get("name",""), r.get("module",""), r.get("app",""),
        r.get("controller",""), r.get("function",""),
        r.get("docstring","") or "", r.get("path",""),
    ]
    if r.get("type") == "doctype":
        for f in r.get("fields",[]):
            parts += [f.get("fieldname",""), f.get("label","") or "", f.get("options","") or ""]
    if r.get("type") == "controller":
        for m in r.get("methods",[]):
            parts += [m.get("name",""), m.get("docstring","") or ""]
    if r.get("type") == "api":
        parts += r.get("args",[])
    if r.get("type") == "hot_file":
        parts.append(r.get("content","")[:500])
    return " ".join(str(p) for p in parts if p)

def score(r: dict, tokens: list[str]) -> int:
    text = record_text(r).lower()
    name = (r.get("name") or r.get("function") or r.get("controller") or r.get("path") or "").lower()
    s = 0
    for t in tokens:
        if t in name:
            s += 5
        elif t in text:
            s += 1
    return s

def search(query: str, top: int = 20, app: str = None, record_type: str = None) -> list[dict]:
    tokens = tokenize(query)
    if not tokens:
        return []
    results = []
    for r in load_corpus():
        if app and r.get("app") != app:
            continue
        if record_type and r.get("type") != record_type:
            continue
        s = score(r, tokens)
        if s > 0:
            results.append((s, r))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:top]]

def format_record(r: dict) -> str:
    """Full multi-line format — use for deep-dive on top hits."""
    t = r.get("type")
    lines = []
    if t == "doctype":
        lines.append(f"[doctype] {r['name']} — app:{r['app']} module:{r.get('module','')}")
        for f in r.get("fields",[]):
            if f.get("fieldname"):
                opts = f" → {f['options']}" if f.get("options") else ""
                req  = " *" if f.get("reqd") else ""
                lines.append(f"  {f['fieldname']} ({f['fieldtype']}){opts}{req}")
    elif t == "controller":
        lines.append(f"[controller] {r['controller']} — {r.get('source','')}")
        for m in r.get("methods",[]):
            args = ", ".join(m.get("args",[]))
            doc  = f" — {m['docstring'][:80]}" if m.get("docstring") else ""
            lines.append(f"  def {m['name']}({args}){doc}")
    elif t == "api":
        args = ", ".join(r.get("args",[]))
        lines.append(f"[api] {r['function']}({args}) — {r.get('source','')}")
        if r.get("docstring"):
            lines.append(f"  {r['docstring'][:120]}")
    elif t == "hot_file":
        lines.append(f"[hot_file] {r['path']} ({r.get('language','')})")
        lines.append(r.get("content","")[:3000])
    elif t == "hooks":
        lines.append(f"[hooks] app:{r['app']}")
        for k, v in list(r.get("hooks",{}).items())[:10]:
            lines.append(f"  {k}: {str(v)[:80]}")
    return "\n".join(lines)


def format_record_compact(r: dict) -> str:
    """One-liner per record — ~70% fewer tokens. Use for initial broad scan."""
    t = r.get("type")
    if t == "doctype":
        fields = [f["fieldname"] for f in r.get("fields", []) if f.get("fieldname")][:8]
        return f"[doctype] {r['name']} ({r['app']}) fields:{','.join(fields)}"
    if t == "controller":
        methods = [m["name"] for m in r.get("methods", [])][:8]
        return f"[ctrl] {r['controller']} ({r.get('source','')}) methods:{','.join(methods)}"
    if t == "api":
        args = ",".join(r.get("args", []))
        return f"[api] {r['function']}({args}) {r.get('source','')}"
    if t == "hot_file":
        return f"[hot_file] {r['path']} ({r.get('language','')})"
    if t == "hooks":
        keys = list(r.get("hooks", {}).keys())[:5]
        return f"[hooks] {r['app']} keys:{','.join(keys)}"
    return f"[{t}] {r.get('name') or r.get('source', '')}"


# ── Skills / prompts library ─────────────────────────────────────────────────

SKILLS_DIRS = [
    Path.home() / ".claude" / "skills",
    Path(".claude") / "skills",
]

def load_skills() -> dict[str, dict]:
    """Return all skills keyed by name: {name, description, content, path}"""
    skills = {}
    for base in SKILLS_DIRS:
        if not base.exists():
            continue
        for skill_dir in sorted(base.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            raw = skill_md.read_text(errors="ignore")
            # Parse frontmatter
            description, name = "", skill_dir.name
            if raw.startswith("---"):
                end = raw.find("---", 3)
                if end != -1:
                    fm = raw[3:end]
                    for line in fm.splitlines():
                        if line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                    content = raw[end+3:].strip()
                else:
                    content = raw
            else:
                content = raw
            skills[name] = {
                "name": name,
                "description": description,
                "content": content,
                "path": str(skill_md),
            }
    return skills


# ── Project info ──────────────────────────────────────────────────────────────

def get_project_info() -> dict:
    apps_path = BENCH_PATH / "apps"
    core = {"frappe","erpnext","hrms","payments","insights","india_compliance",
            "microsoft_integration","atsl_migrator","grievance","techademy_erp"}
    custom_apps = []
    if apps_path.exists():
        custom_apps = [p.name for p in sorted(apps_path.iterdir())
                       if p.is_dir() and p.name not in core]
    sites = []
    sites_path = BENCH_PATH / "sites"
    if sites_path.exists():
        sites = [p.name for p in sites_path.iterdir()
                 if p.is_dir() and not p.name.startswith("assets")]
    return {
        "bench_path": str(BENCH_PATH),
        "corpus_path": str(CORPUS_PATH),
        "corpus_records": len(load_corpus()),
        "custom_apps": custom_apps,
        "sites": sites,
        "test_command": "bench run-tests --app <app> --doctype <doctype>",
        "commit_convention": "Conventional Commits (feat/fix/chore/docs)",
    }


# ── MCP server (stdio) ────────────────────────────────────────────────────────

def run_mcp():
    from fastmcp import FastMCP

    mcp = FastMCP(
        name="corpus-search",
        instructions="Search the Frappe project corpus for DocTypes, APIs, controllers, and hot files."
    )

    @mcp.tool()
    def search_corpus(query: str, top: int = 10, app: str = "", record_type: str = "") -> str:
        """Search corpus.jsonl for DocTypes, APIs, controllers relevant to a task. Returns full detail.
        Prefer search_corpus_compact for broad scans and search_corpus_delta for follow-up searches."""
        results = search(query, top=top,
                         app=app or None,
                         record_type=record_type or None)
        if not results:
            return f"No results for: {query}"
        _session_seen.update(r.get("source", "") for r in results)
        return f"# Corpus: '{query}' — {len(results)} results\n\n" + \
               "\n\n".join(format_record(r) for r in results)

    @mcp.tool()
    def search_corpus_compact(query: str, top: int = 15, app: str = "", record_type: str = "") -> str:
        """Compact one-liner per record (~70% fewer tokens). Use for initial broad scan to identify
        which DocTypes/controllers are relevant, then call search_corpus on specific names."""
        results = search(query, top=top,
                         app=app or None,
                         record_type=record_type or None)
        if not results:
            return f"No results for: {query}"
        _session_seen.update(r.get("source", "") for r in results)
        lines = [format_record_compact(r) for r in results]
        return f"# Corpus compact: '{query}' — {len(results)} results\n" + "\n".join(lines)

    @mcp.tool()
    def search_corpus_delta(query: str, top: int = 10, app: str = "", record_type: str = "") -> str:
        """Like search_corpus but skips sources already returned this session (deduplication).
        Use for follow-up searches to avoid re-sending context already in the conversation."""
        results = search(query, top=top,
                         app=app or None,
                         record_type=record_type or None)
        new_results = [r for r in results if r.get("source", "") not in _session_seen]
        if not new_results:
            seen_count = len(results) - len(new_results)
            return f"No new results for: '{query}' (all {seen_count} matches already in session)"
        _session_seen.update(r.get("source", "") for r in new_results)
        return f"# Corpus delta: '{query}' — {len(new_results)} new results\n\n" + \
               "\n\n".join(format_record(r) for r in new_results)

    @mcp.tool()
    def reset_session_cache() -> str:
        """Clear the session deduplication cache. Call this when starting a new task
        so delta searches return full results again."""
        count = len(_session_seen)
        _session_seen.clear()
        return f"Session cache cleared ({count} sources removed)"

    @mcp.tool()
    def get_hot_file(path: str) -> str:
        """Get the full content of a frequently-used file embedded in the corpus."""
        for r in load_corpus():
            if r.get("type") == "hot_file" and r.get("path") == path:
                content = r.get("content","")
                trunc   = " [TRUNCATED]" if r.get("truncated") else ""
                return f"# {path}{trunc}\n\n```{r.get('language','')}\n{content}\n```"
        # fallback: read from disk
        full = BENCH_PATH / path
        if full.exists():
            return full.read_text(errors="ignore")[:15000]
        return f"File not found in corpus or disk: {path}"

    @mcp.tool()
    def list_doctypes(app: str = "") -> str:
        """List all DocTypes in the corpus, optionally filtered by app."""
        records = [r for r in load_corpus()
                   if r.get("type") == "doctype"
                   and (not app or r.get("app") == app)]
        lines = [f"{r['name']} — app:{r['app']} module:{r.get('module','')}"
                 for r in sorted(records, key=lambda x: x.get("app",""))]
        return f"{len(lines)} DocTypes:\n" + "\n".join(lines)

    @mcp.tool()
    def project_info() -> str:
        """Get bench path, apps, sites, test command, and corpus stats."""
        info = get_project_info()
        return json.dumps(info, indent=2)

    @mcp.tool()
    def list_prompts() -> str:
        """List all available skills/prompts with their descriptions."""
        skills = load_skills()
        lines = [f"/{name} — {s['description']}" for name, s in sorted(skills.items())]
        return f"{len(lines)} skills available:\n" + "\n".join(lines)

    @mcp.tool()
    def get_prompt(skill_name: str) -> str:
        """Get the full instructions for a skill to use in any AI tool. skill_name e.g. 'debug', 'bank-api'."""
        skills = load_skills()
        skill = skills.get(skill_name)
        if not skill:
            available = ", ".join(sorted(skills.keys()))
            return f"Skill '{skill_name}' not found. Available: {available}"
        return f"# /{skill['name']}\n{skill['description']}\n\n{skill['content']}"

    mcp.run()


# ── HTTP server (for non-MCP tools) ──────────────────────────────────────────

def run_http(port: int = 7070):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # silence request logs

        def _json(self, data, status=200):
            body = json.dumps(data, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            qs     = parse_qs(parsed.query)

            if parsed.path == "/search":
                query   = qs.get("q",[""])[0]
                top     = int(qs.get("top",["10"])[0])
                app     = qs.get("app",[""])[0] or None
                rtype   = qs.get("type",[""])[0] or None
                compact = qs.get("compact",[""])[0] == "1"
                delta   = qs.get("delta",[""])[0] == "1"
                results = search(query, top=top, app=app, record_type=rtype)
                if delta:
                    results = [r for r in results if r.get("source","") not in _session_seen]
                _session_seen.update(r.get("source","") for r in results)
                if compact:
                    lines = [format_record_compact(r) for r in results]
                    body  = f"# Corpus: '{query}' — {len(results)} results\n" + "\n".join(lines)
                    body  = body.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", len(body))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self._json({"query": query, "count": len(results), "results": results})

            elif parsed.path == "/hot_file":
                path    = qs.get("path",[""])[0]
                for r in load_corpus():
                    if r.get("type") == "hot_file" and r.get("path") == path:
                        self._json(r)
                        return
                self._json({"error": f"not found: {path}"}, 404)

            elif parsed.path == "/doctypes":
                app    = qs.get("app",[""])[0] or None
                records = [r for r in load_corpus()
                           if r.get("type") == "doctype"
                           and (not app or r.get("app") == app)]
                self._json({"count": len(records), "doctypes": records})

            elif parsed.path == "/project_info":
                self._json(get_project_info())

            elif parsed.path == "/system-prompt":
                # Returns the universal system prompt for Codex/Antigravity/Gemini
                sp_path = Path(__file__).parent / "system_prompt_universal.md"
                if sp_path.exists():
                    body = sp_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", len(body))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self._json({"error": "system_prompt_universal.md not found"}, 404)

            elif parsed.path == "/prompts":
                skills = load_skills()
                name = qs.get("name", [""])[0]
                if name:
                    skill = skills.get(name)
                    if skill:
                        # Return as plain text for easy copy-paste into any AI
                        body = f"# /{skill['name']}\n{skill['description']}\n\n{skill['content']}".encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/plain; charset=utf-8")
                        self.send_header("Content-Length", len(body))
                        self.end_headers()
                        self.wfile.write(body)
                    else:
                        self._json({"error": f"Skill '{name}' not found",
                                    "available": sorted(skills.keys())}, 404)
                else:
                    self._json({
                        "skills": [
                            {"name": s["name"], "description": s["description"]}
                            for s in sorted(skills.values(), key=lambda x: x["name"])
                        ],
                        "usage": "GET /prompts?name=<skill> to get full instructions"
                    })

            else:
                self._json({
                    "endpoints": [
                        "/system-prompt                          ← paste into Codex/Antigravity/Gemini",
                        "/search?q=&top=10&app=&type=",
                        "/search?q=&compact=1                   ← one-liner per record (~70% fewer tokens)",
                        "/search?q=&delta=1                     ← skip already-seen sources this session",
                        "/hot_file?path=",
                        "/doctypes?app=",
                        "/project_info",
                        "/prompts",
                        "/prompts?name=<skill-name>",
                    ]
                })

    print(f"Corpus HTTP server running on http://localhost:{port}", flush=True)
    print(f"  Corpus: {CORPUS_PATH} ({len(load_corpus())} records)", flush=True)
    HTTPServer(("localhost", port), Handler).serve_forever()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run HTTP server instead of MCP stdio")
    parser.add_argument("--port", type=int, default=7070)
    parser.add_argument("--test", action="store_true", help="Run a quick self-test and exit")
    args = parser.parse_args()

    if args.test:
        records = load_corpus()
        print(f"Corpus loaded: {len(records)} records from {CORPUS_PATH}")
        results = search("payout approval", top=5)
        print(f"Search 'payout approval': {len(results)} results")
        for r in results:
            print(f"  {r.get('type')} — {r.get('name') or r.get('function') or r.get('controller') or r.get('path')}")
        info = get_project_info()
        print(f"Apps: {info['custom_apps']}")
        print("Self-test OK")
    elif args.http:
        run_http(args.port)
    else:
        run_mcp()
