#!/usr/bin/env python3
"""
Search corpus.jsonl and return only relevant records for a task.
Keeps Phase 1 context small instead of loading all 1,761 records.

Usage:
    python3 search_corpus.py "add fee calculation to escrow settlement"
    python3 search_corpus.py "payout approval workflow" --app p2p_escrow
    python3 search_corpus.py "whitelisted apis for batch" --type api
    python3 search_corpus.py "escrow merchant" --top 10
"""

import json
import os
import re
import argparse
from pathlib import Path

def _find_corpus() -> Path:
    """Find corpus.jsonl — check CWD, then walk up, then FRAPPE_BENCH_PATH env."""
    env_path = os.environ.get("CORPUS_PATH")
    if env_path:
        return Path(env_path)
    for path in [Path.cwd(), *Path.cwd().parents]:
        candidate = path / "corpus.jsonl"
        if candidate.exists():
            return candidate
    return Path.cwd() / "corpus.jsonl"

CORPUS_PATH = _find_corpus()

STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "to", "in", "on", "of",
    "add", "create", "build", "make", "new", "get", "set", "update",
    "with", "this", "that", "from", "into", "is", "it", "be", "as",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]


def record_text(record: dict) -> str:
    """Flatten a record into searchable text."""
    parts = [
        record.get("name", ""),
        record.get("module", ""),
        record.get("app", ""),
        record.get("controller", ""),
        record.get("function", ""),
        record.get("docstring", "") or "",
    ]

    if record.get("type") == "doctype":
        for f in record.get("fields", []):
            parts += [f.get("fieldname", ""), f.get("label", "") or "", f.get("options", "") or ""]

    if record.get("type") == "controller":
        for m in record.get("methods", []):
            parts += [m.get("name", ""), m.get("docstring", "") or ""]

    if record.get("type") == "api":
        parts += record.get("args", [])

    if record.get("type") == "hooks":
        parts += list(record.get("hooks", {}).keys())

    return " ".join(str(p) for p in parts if p)


def score(record: dict, tokens: list[str]) -> int:
    text = record_text(record).lower()
    text_tokens = tokenize(text)

    s = 0
    name = (record.get("name") or record.get("function") or record.get("controller") or "").lower()

    for token in tokens:
        if token in name:
            s += 5          # strong signal: query token in record name
        elif token in text:
            s += 1          # weak signal: anywhere in record

        # bonus: exact multi-word match in name
        if len(tokens) > 1:
            phrase = "_".join(tokens)
            if phrase in name.replace(" ", "_"):
                s += 10

    return s


def search(query: str, app: str | None, record_type: str | None, top: int) -> list[dict]:
    tokens = tokenize(query)
    if not tokens:
        return []

    results = []
    with CORPUS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue

            if app and record.get("app") != app:
                continue
            if record_type and record.get("type") != record_type:
                continue

            s = score(record, tokens)
            if s > 0:
                results.append((s, record))

    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:top]]


def format_record(record: dict) -> str:
    t = record.get("type")
    lines = []

    if t == "doctype":
        lines.append(f"[doctype] {record['name']} — app:{record['app']} module:{record['module']}")
        lines.append(f"  submittable:{record['is_submittable']} child_table:{record['is_child_table']}")
        for f in record.get("fields", []):
            if f.get("fieldname"):
                opts = f" → {f['options']}" if f.get("options") else ""
                req = " *" if f.get("reqd") else ""
                lines.append(f"  {f['fieldname']} ({f['fieldtype']}){opts}{req}")

    elif t == "controller":
        lines.append(f"[controller] {record['controller']} — {record['source']}")
        for m in record.get("methods", []):
            args = ", ".join(m.get("args", []))
            doc = f" — {m['docstring'][:80]}" if m.get("docstring") else ""
            lines.append(f"  def {m['name']}({args}){doc}")

    elif t == "api":
        args = ", ".join(record.get("args", []))
        lines.append(f"[api] {record['function']}({args}) — {record['source']}")
        if record.get("docstring"):
            lines.append(f"  {record['docstring'][:120]}")

    elif t == "hooks":
        lines.append(f"[hooks] app:{record['app']}")
        for k, v in record.get("hooks", {}).items():
            lines.append(f"  {k}: {str(v)[:80]}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search corpus.jsonl for relevant context")
    parser.add_argument("query", help="Task description or keywords")
    parser.add_argument("--app", help="Filter by app name (e.g. p2p_escrow)")
    parser.add_argument("--type", dest="record_type", choices=["doctype", "controller", "api", "hooks"],
                        help="Filter by record type")
    parser.add_argument("--top", type=int, default=20, help="Max records to return (default: 20)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON lines instead of formatted text")
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        print(f"ERROR: corpus.jsonl not found at {CORPUS_PATH}")
        print("Run: python3 generate_corpus.py")
        return

    results = search(args.query, args.app, args.record_type, args.top)

    if not results:
        print(f"No results for: {args.query}")
        return

    print(f"# Corpus search: '{args.query}' — {len(results)} results\n")

    if args.json:
        for r in results:
            print(json.dumps(r))
    else:
        for r in results:
            print(format_record(r))
            print()


if __name__ == "__main__":
    main()
