#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$HOME/.venvs/chub"
BIN_DIR="$HOME/.local/bin"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"
mkdir -p "$BIN_DIR"
ln -sf "$REPO_DIR/chub" "$BIN_DIR/chub"
"$BIN_DIR/chub" --help
mkdir -p "$HOME/context-docs/skills" "$HOME/context-docs/notes" "$HOME/context-docs/api"
cp -rn "$REPO_DIR/examples/sample-docs/." "$HOME/context-docs/" 2>/dev/null || true
cp -rn "$REPO_DIR/examples/sample-skills/." "$HOME/context-docs/skills/" 2>/dev/null || true
"$BIN_DIR/chub" init
"$BIN_DIR/chub" add "$HOME/context-docs"
echo "Setup complete. Run: chub stats"
