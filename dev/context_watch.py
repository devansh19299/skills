#!/usr/bin/env python3
"""
Context Watch — lightweight context usage tracker.

Reads the Claude Code session transcript to get actual API token counts
(from the `usage` field in assistant messages), then outputs a one-liner
showing how full the context window is.

Inspired by ruflo's Context Autopilot (context-persistence-hook.mjs).

Usage:
    python3 context_watch.py                  # one-shot report
    python3 context_watch.py --hook           # JSON output for UserPromptSubmit hook

As a UserPromptSubmit hook in .claude/settings.json:
    {
      "type": "command",
      "command": "python3 /path/to/context_watch.py --hook",
      "timeout": 3000
    }
"""

import json
import os
import sys
from pathlib import Path

CONTEXT_WINDOW = int(os.environ.get("CLAUDE_CONTEXT_WINDOW", "200000"))
WARN_PCT = 0.70
CRIT_PCT = 0.85
CHARS_PER_TOKEN = 3.5


def find_transcript() -> Path | None:
    # Claude Code sets this env var when running hooks
    env_path = os.environ.get("CLAUDE_SESSION_TRANSCRIPT")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    # Also try reading from stdin (hook input) for session_id based lookup
    return None


def parse_token_usage(transcript_path: Path) -> dict:
    """Extract actual token counts from the last assistant message's usage field."""
    last_input = last_cache_read = last_cache_create = 0
    turns = 0
    total_chars = 0

    try:
        content = transcript_path.read_text(errors="ignore")
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
                msg = parsed.get("message") or parsed
                role = msg.get("role") or parsed.get("type", "")
                usage = msg.get("usage")

                if usage and role == "assistant":
                    inp = usage.get("input_tokens", 0)
                    cr = usage.get("cache_read_input_tokens", 0)
                    cc = usage.get("cache_creation_input_tokens", 0)
                    if inp + cr + cc > 0:
                        last_input, last_cache_read, last_cache_create = inp, cr, cc

                if role in ("user", "assistant"):
                    turns += 1
                    c = msg.get("content", "")
                    if isinstance(c, str):
                        total_chars += len(c)
                    elif isinstance(c, list):
                        for block in c:
                            if isinstance(block, dict):
                                total_chars += len(block.get("text", "") or "")
            except Exception:
                continue
    except Exception:
        pass

    actual_total = last_input + last_cache_read + last_cache_create
    if actual_total > 0:
        return {"tokens": actual_total, "turns": turns // 2, "method": "api",
                "input": last_input, "cache_read": last_cache_read, "cache_create": last_cache_create}

    estimated = int(total_chars / CHARS_PER_TOKEN)
    return {"tokens": estimated, "turns": turns // 2, "method": "estimated"}


def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def build_bar(pct: float, width: int = 20) -> str:
    filled = round(pct * width)
    empty = width - filled
    ch = "!" if pct >= CRIT_PCT else "#" if pct >= WARN_PCT else "="
    return f"[{ch * filled}{'-' * empty}]"


def main():
    hook_mode = "--hook" in sys.argv

    transcript = find_transcript()
    if not transcript:
        if hook_mode:
            sys.exit(0)
        print("[context_watch] No transcript found (set CLAUDE_SESSION_TRANSCRIPT)")
        return

    usage = parse_token_usage(transcript)
    tokens = usage["tokens"]
    turns = usage["turns"]
    pct = min(tokens / CONTEXT_WINDOW, 1.0)
    bar = build_bar(pct)
    method = "*" if usage["method"] == "estimated" else ""

    status = "OK"
    advice = ""
    if pct >= CRIT_PCT:
        status = "CRITICAL"
        turns_left = max(0, int((1.0 - pct) / 0.03))
        advice = f" — ~{turns_left} turns left, run /handoff then /clear"
    elif pct >= WARN_PCT:
        status = "WARNING"
        advice = " — keep responses concise"

    line = f"[Context {bar} {pct*100:.0f}%{method} — {format_tokens(tokens)}/{format_tokens(CONTEXT_WINDOW)} tokens, {turns} turns | {status}{advice}]"

    if hook_mode:
        # Output as UserPromptSubmit additionalContext injection
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": line,
            }
        }
        print(json.dumps(out))
    else:
        print(line)

    if usage["method"] == "api":
        cache_pct = (usage["cache_read"] / tokens * 100) if tokens else 0
        if not hook_mode:
            print(f"  cache hit: {cache_pct:.0f}%  ({format_tokens(usage['cache_read'])} read + {format_tokens(usage['cache_create'])} created)")


if __name__ == "__main__":
    main()
