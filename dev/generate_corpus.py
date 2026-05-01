#!/usr/bin/env python3
"""
Generates corpus.jsonl from custom Frappe apps.
Each line is a self-contained JSON object describing a DocType, controller, hook, or API.

Usage:
    python3 generate_corpus.py
    python3 generate_corpus.py --apps p2p_escrow p2p_admin
    python3 generate_corpus.py --output my_corpus.jsonl
"""

import ast
import json
import argparse
import os
from pathlib import Path

def _find_bench() -> Path:
    """Walk up from CWD to find a Frappe bench (directory containing apps/ and sites/)."""
    cwd = Path(os.environ.get("FRAPPE_BENCH_PATH", "")).resolve() if os.environ.get("FRAPPE_BENCH_PATH") else None
    if cwd and (cwd / "apps").exists():
        return cwd
    for path in [Path.cwd(), *Path.cwd().parents]:
        if (path / "apps").exists() and (path / "sites").exists():
            return path
    # fallback
    return Path("/workspace/development/canopi-bench")

BENCH_PATH = _find_bench()
APPS_PATH = BENCH_PATH / "apps"

def _default_apps() -> list[str]:
    """Return all apps in the bench, excluding core Frappe apps."""
    core = {"frappe", "erpnext", "hrms", "payments", "insights", "india_compliance",
            "microsoft_integration", "atsl_migrator", "grievance", "techademy_erp"}
    if not APPS_PATH.exists():
        return []
    return [p.name for p in sorted(APPS_PATH.iterdir()) if p.is_dir() and p.name not in core]

CUSTOM_APPS = _default_apps()


def extract_doctype(json_path: Path) -> dict | None:
    try:
        data = json.loads(json_path.read_text())
    except Exception:
        return None

    fields = [
        {
            "fieldname": f.get("fieldname"),
            "fieldtype": f.get("fieldtype"),
            "label": f.get("label"),
            "options": f.get("options"),
            "reqd": bool(f.get("reqd")),
            "in_list_view": bool(f.get("in_list_view")),
        }
        for f in data.get("fields", [])
        if f.get("fieldname")
    ]

    return {
        "type": "doctype",
        "name": data.get("name"),
        "module": data.get("module"),
        "app": json_path.parts[json_path.parts.index("apps") + 1],
        "is_submittable": bool(data.get("is_submittable")),
        "is_child_table": bool(data.get("istable")),
        "track_changes": bool(data.get("track_changes")),
        "fields": fields,
        "permissions": [
            {"role": p.get("role"), "read": p.get("read"), "write": p.get("write")}
            for p in data.get("permissions", [])
        ],
        "source": str(json_path.relative_to(BENCH_PATH)),
    }


def extract_controller(py_path: Path) -> dict | None:
    try:
        source = py_path.read_text()
        tree = ast.parse(source)
    except Exception:
        return None

    app = py_path.parts[py_path.parts.index("apps") + 1]
    methods = []
    controller_name = None

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            controller_name = node.name
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    docstring = ast.get_docstring(item) or ""
                    args = [a.arg for a in item.args.args if a.arg != "self"]
                    methods.append({
                        "name": item.name,
                        "args": args,
                        "docstring": docstring[:200] if docstring else None,
                    })

    if not controller_name:
        return None

    return {
        "type": "controller",
        "app": app,
        "controller": controller_name,
        "methods": methods,
        "source": str(py_path.relative_to(BENCH_PATH)),
    }


def extract_whitelisted_apis(py_path: Path) -> list[dict]:
    try:
        source = py_path.read_text()
        tree = ast.parse(source)
    except Exception:
        return []

    app = py_path.parts[py_path.parts.index("apps") + 1]
    apis = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        decorators = [
            ast.unparse(d) if hasattr(ast, "unparse") else getattr(d, "id", "")
            for d in node.decorator_list
        ]
        is_whitelisted = any("whitelist" in d for d in decorators)
        if not is_whitelisted:
            continue

        args = [a.arg for a in node.args.args]
        docstring = ast.get_docstring(node) or ""

        apis.append({
            "type": "api",
            "app": app,
            "function": node.name,
            "args": args,
            "docstring": docstring[:300] if docstring else None,
            "decorators": decorators,
            "source": str(py_path.relative_to(BENCH_PATH)),
        })

    return apis


def extract_hooks(hooks_path: Path) -> dict | None:
    try:
        source = hooks_path.read_text()
        tree = ast.parse(source)
    except Exception:
        return None

    app = hooks_path.parts[hooks_path.parts.index("apps") + 1]
    hooks = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        hooks[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        hooks[target.id] = "__complex__"

    return {
        "type": "hooks",
        "app": app,
        "hooks": hooks,
        "source": str(hooks_path.relative_to(BENCH_PATH)),
    }


def generate_corpus(apps: list[str], output: Path):
    records = []
    stats = {"doctypes": 0, "controllers": 0, "apis": 0, "hooks": 0, "skipped": 0}

    for app_name in apps:
        app_path = APPS_PATH / app_name
        if not app_path.exists():
            print(f"  [skip] {app_name} — not found")
            continue

        print(f"  Processing {app_name}...")

        # DocType schemas
        for json_path in sorted(app_path.rglob("*.json")):
            if "/doctype/" not in str(json_path):
                continue
            record = extract_doctype(json_path)
            if record:
                records.append(record)
                stats["doctypes"] += 1

        # Controllers
        for py_path in sorted(app_path.rglob("*.py")):
            if "/doctype/" not in str(py_path):
                continue
            record = extract_controller(py_path)
            if record:
                records.append(record)
                stats["controllers"] += 1

        # Whitelisted APIs (all python files)
        for py_path in sorted(app_path.rglob("*.py")):
            apis = extract_whitelisted_apis(py_path)
            records.extend(apis)
            stats["apis"] += len(apis)

        # Hooks
        hooks_path = app_path / app_name / "hooks.py"
        if hooks_path.exists():
            record = extract_hooks(hooks_path)
            if record:
                records.append(record)
                stats["hooks"] += 1

    with output.open("w") as f:
        for record in records:
            f.write(json.dumps(record, default=str) + "\n")

    return stats, len(records)


def main():
    parser = argparse.ArgumentParser(description="Generate corpus.jsonl for Frappe apps")
    parser.add_argument("--apps", nargs="+", default=CUSTOM_APPS, help="App names to include")
    parser.add_argument("--output", default="corpus.jsonl", help="Output file path")
    args = parser.parse_args()

    output = Path(args.output)
    print(f"Generating corpus from: {', '.join(args.apps)}")
    print(f"Output: {output}\n")

    stats, total = generate_corpus(args.apps, output)

    print(f"\nDone. {total} records written to {output}")
    print(f"  DocTypes:    {stats['doctypes']}")
    print(f"  Controllers: {stats['controllers']}")
    print(f"  APIs:        {stats['apis']}")
    print(f"  Hooks:       {stats['hooks']}")
    size_kb = output.stat().st_size / 1024
    print(f"  File size:   {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
