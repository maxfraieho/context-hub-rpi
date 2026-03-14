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
