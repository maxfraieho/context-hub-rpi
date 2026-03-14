#!/bin/bash
set -euo pipefail

CHUB_BIN="${CHUB_BIN:-$HOME/.local/bin/chub}"
TEMP_DOC="$(mktemp --suffix=.md)"
ORIGINAL_HOME="$HOME"
BACKUP_CHUB=""

cleanup() {
  rm -f "$TEMP_DOC"
  if [[ -n "$BACKUP_CHUB" && -d "$BACKUP_CHUB" ]]; then
    rm -rf "$ORIGINAL_HOME/.chub"
    mv "$BACKUP_CHUB" "$ORIGINAL_HOME/.chub"
  else
    rm -rf "$ORIGINAL_HOME/.chub"
  fi
}

fail() {
  echo "FAIL: $1"
  cleanup
  exit 1
}

run_chub() {
  "$CHUB_BIN" "$@"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "$haystack" != *"$needle"* ]]; then
    fail "expected output to contain: $needle"
  fi
}

trap cleanup EXIT

[[ -x "$CHUB_BIN" ]] || fail "chub binary not found or not executable at $CHUB_BIN"

if [[ -e "$ORIGINAL_HOME/.chub" ]]; then
  BACKUP_CHUB="$(mktemp -d)"
  rm -rf "$BACKUP_CHUB"
  mv "$ORIGINAL_HOME/.chub" "$BACKUP_CHUB"
fi

cat >"$TEMP_DOC" <<'EOF'
# Smoke Test Doc

alpha bravo context keyword
EOF

run_chub init >/dev/null

run_chub add "$TEMP_DOC" >/dev/null

list_output="$(run_chub list)"
assert_contains "$list_output" "Smoke Test Doc"

doc_count="$(python3 - <<'PY'
from pathlib import Path
import json
home = Path.home()
data = json.loads((home / ".chub" / "index.json").read_text())
print(len(data))
PY
)"
[[ "$doc_count" == "1" ]] || fail "expected exactly 1 indexed doc, got $doc_count"

doc_id="$(python3 - <<'PY'
from pathlib import Path
import json
home = Path.home()
data = json.loads((home / ".chub" / "index.json").read_text())
print(data[0]["id"])
PY
)"

search_output="$(run_chub search keyword)"
assert_contains "$search_output" "$doc_id"
assert_contains "$search_output" "alpha bravo context keyword"

get_output="$(run_chub get "$doc_id")"
assert_contains "$get_output" "alpha bravo context keyword"

annotate_output="$(run_chub annotate "$doc_id" "test note")"
assert_contains "$annotate_output" "Annotated $doc_id"

annotations_output="$(run_chub annotate --list)"
assert_contains "$annotations_output" "test note"

stats_output="$(run_chub stats)"
assert_contains "$stats_output" "total docs: 1"
assert_contains "$stats_output" "annotation count: 1"

echo "PASS"
