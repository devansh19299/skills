#!/bin/bash
# Bootstrap all skills from github.com/devansh19299/skills into ~/.claude/skills/
#
# Usage (any container, one command):
#   curl -fsSL https://raw.githubusercontent.com/devansh19299/skills/main/dev/bootstrap_dev_skill.sh | bash
#
# Then set up corpus in your project:
#   cd /your/frappe/bench
#   bash ~/.claude/skills/dev/install.sh

set -e

SKILLS_DEST="$HOME/.claude/skills"
REPO="https://github.com/devansh19299/skills.git"
TMP_DIR=$(mktemp -d)

echo "=== Installing skills from $REPO ==="

# Clone the repo (depth 1 — just the latest)
git clone --depth 1 --quiet "$REPO" "$TMP_DIR/skills"

# Install all skills
mkdir -p "$SKILLS_DEST"
for skill_dir in "$TMP_DIR/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  [[ "$skill_name" == .* ]] && continue
  mkdir -p "$SKILLS_DEST/$skill_name"
  cp "$skill_dir/SKILL.md" "$SKILLS_DEST/$skill_name/SKILL.md"
  echo "  [ok] /$skill_name"
done

# Install dev corpus tools
cp "$TMP_DIR/skills/dev/generate_corpus.py"       "$SKILLS_DEST/dev/"
cp "$TMP_DIR/skills/dev/search_corpus.py"         "$SKILLS_DEST/dev/"
cp "$TMP_DIR/skills/dev/corpus_server.py"         "$SKILLS_DEST/dev/"
cp "$TMP_DIR/skills/dev/context_watch.py"         "$SKILLS_DEST/dev/"
cp "$TMP_DIR/skills/dev/install.sh"               "$SKILLS_DEST/dev/"
cp "$TMP_DIR/skills/dev/system_prompt_universal.md" "$SKILLS_DEST/dev/"
echo "  [ok] corpus tools (generate, search, server, context_watch)"

# Apply workspace settings (autocompaction + skill budget fraction)
SETTINGS_DIR="$HOME/.claude"
mkdir -p "$SETTINGS_DIR"
if [ ! -f "$SETTINGS_DIR/settings.json" ]; then
  cat > "$SETTINGS_DIR/settings.json" << 'JSON'
{
  "skillListingBudgetFraction": 0.06,
  "env": {
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"
  }
}
JSON
  echo "  [ok] ~/.claude/settings.json created (autocompaction + skill budget)"
else
  echo "  [skip] ~/.claude/settings.json already exists"
  echo "         Add manually: skillListingBudgetFraction: 0.06, CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 50"
fi

# Install fastmcp for MCP server
pip install fastmcp -q 2>/dev/null && echo "  [ok] fastmcp installed" || echo "  [warn] fastmcp install failed — MCP server won't work without it"

# Cleanup
rm -rf "$TMP_DIR"

echo ""
echo "=== Skills installed at $SKILLS_DEST ==="
ls "$SKILLS_DEST/"
echo ""
echo "Next: set up corpus in your Frappe bench:"
echo "  cd /your/frappe/bench"
echo "  bash ~/.claude/skills/dev/install.sh"
