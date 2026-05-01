#!/bin/bash
# Install the /dev skill and corpus tools into a new container.
#
# Usage:
#   bash install.sh                  # install globally + set up current project
#   bash install.sh --global-only    # only install the Claude skill, skip project hooks

set -e

SKILL_DIR="$HOME/.claude/skills/dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_ONLY=false

for arg in "$@"; do
  [[ "$arg" == "--global-only" ]] && GLOBAL_ONLY=true
done

echo "=== Installing /dev skill ==="

# 1. Copy skill files to ~/.claude/skills/dev/
mkdir -p "$SKILL_DIR"
cp "$SCRIPT_DIR/SKILL.md"             "$SKILL_DIR/SKILL.md"
cp "$SCRIPT_DIR/generate_corpus.py"   "$SKILL_DIR/generate_corpus.py"
cp "$SCRIPT_DIR/search_corpus.py"     "$SKILL_DIR/search_corpus.py"
cp "$SCRIPT_DIR/install.sh"           "$SKILL_DIR/install.sh"
echo "  [ok] Skill installed at $SKILL_DIR"

if $GLOBAL_ONLY; then
  echo ""
  echo "Done (global only). Run without --global-only inside a project to set up hooks."
  exit 0
fi

# 2. Set up project corpus tools in CWD
echo ""
echo "=== Setting up corpus in $(pwd) ==="

cp "$SKILL_DIR/generate_corpus.py" ./generate_corpus.py
cp "$SKILL_DIR/search_corpus.py"   ./search_corpus.py
echo "  [ok] generate_corpus.py and search_corpus.py copied to $(pwd)"

# 3. Generate the initial corpus
echo "  Generating corpus.jsonl..."
python3 generate_corpus.py
echo "  [ok] corpus.jsonl generated"

# 4. Set up Claude Code project hook (auto-regenerate on file edits)
mkdir -p .claude/hooks

cat > .claude/hooks/refresh_corpus.sh << 'HOOK'
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | python3 -c "
import json, sys
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
print(inp.get('file_path', inp.get('path', '')))
" 2>/dev/null)

if [[ "$file_path" != *"/apps/"* ]]; then exit 0; fi
if [[ "$file_path" != *.py && "$file_path" != *.json ]]; then exit 0; fi

echo "[corpus] Change in $file_path — regenerating corpus.jsonl..." >&2
python3 "$(dirname "$0")/../../generate_corpus.py" >&2
echo "[corpus] Done." >&2
HOOK

chmod +x .claude/hooks/refresh_corpus.sh
echo "  [ok] PostToolUse hook installed at .claude/hooks/refresh_corpus.sh"

# 5. Create .claude/settings.json if it doesn't exist
if [ ! -f .claude/settings.json ]; then
  cat > .claude/settings.json << 'JSON'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/refresh_corpus.sh"
          }
        ]
      }
    ]
  }
}
JSON
  echo "  [ok] .claude/settings.json created"
else
  echo "  [skip] .claude/settings.json already exists — add hook manually if needed"
fi

echo ""
echo "=== All done ==="
echo "  /dev skill is ready. Type /dev <task description> to start."
