# context-hub-rpi

`context-hub-rpi` is a local-first context registry CLI for AI agents running on Raspberry Pi 3B class hardware and other weak servers.

It is a lightweight alternative to Andrew Ng's `context-hub`: no Node.js runtime, no network dependency, and docs that match the implementation in this repository.

## Why

- Local-first: files stay on disk where they already live.
- Lightweight: no daemon, no background RAM cost when idle.
- Simple: pure Python CLI with JSON storage in `~/.chub/`.
- Agent-friendly: `chub get <id>` prints clean text to stdout for piping into Claude, Codex, or other tools.

## Install

```bash
python3 -m venv ~/.venvs/chub
~/.venvs/chub/bin/pip install -r requirements.txt
mkdir -p ~/.local/bin
ln -sf "$(pwd)/chub" ~/.local/bin/chub
~/.local/bin/chub --help
```

If `~/.local/bin` is not in your `PATH`, add it in your shell profile.

## Quick Start

```bash
chub init
chub add ./docs
chub search query
chub get <id>
```

Typical workflow:

```bash
chub init
chub add ./README.md
chub list
chub search local-first
chub annotate <id> "Useful for agent bootstrap context"
chub stats
```

## Commands

### `chub init`

Create the local registry directory and JSON files at `~/.chub/`.

```bash
chub init
```

Example output:

```text
Initialized context registry at /home/you/.chub
```

### `chub add <path>`

Index one `.md` or `.txt` file, or recursively index a directory. Files are discovered with `rglob()`. If the target directory has a `.gitignore`, matching files are skipped.

Supported file types:

- `.md`
- `.txt`

Examples:

```bash
chub add ./README.md
chub add ./docs
chub add ~/notes
```

Example output:

```text
Added 3 document(s); skipped 1 already indexed.
```

### `chub list`

Print a table of indexed documents.

```bash
chub list
```

Columns:

- `id`
- `title`
- `path`
- `tags`

`title` is the first non-empty line of the file, with leading `#` stripped. `tags` default to the parent directory name.

### `chub search <query>`

Search document titles and file content. Content matches include one line of context before and after each hit.

```bash
chub search context
chub search "API token"
```

Example output:

```text
[8f3c1d2a] context-hub-rpi :: /home/you/context-hub-rpi/README.md
title match
5: `context-hub-rpi` is a local-first context registry CLI for AI agents
6: running on Raspberry Pi 3B class hardware and other weak servers.
```

Exit code is `1` when nothing matches.

### `chub get <id>`

Print the full document content to stdout.

```bash
chub get 8f3c1d2a
```

This is the cleanest way to pipe indexed text into an agent prompt.

### `chub annotate <id> <note>`

Append a plain-text annotation to a document.

```bash
chub annotate 8f3c1d2a "Use this during repo onboarding"
```

Example output:

```text
Annotated 8f3c1d2a
```

### `chub annotate --list`

List all stored annotations.

```bash
chub annotate --list
```

Example output:

```text
[8f3c1d2a] context-hub-rpi
- Use this during repo onboarding
```

### `chub stats`

Show total indexed docs, total indexed size, annotation count, and storage path.

```bash
chub stats
```

Example output:

```text
total docs: 3
total size: 18.4 KB
annotation count: 1
path: /home/you/.chub
```

## Storage

`chub` stores only registry metadata and annotations:

- `~/.chub/index.json`
- `~/.chub/annotations.json`

Indexed files stay in place. `chub` does not copy them into a database.

## RAM Usage

| State | Approx. RAM |
| --- | ---: |
| Idle | 0 MB |
| Indexing | ~30 MB |
| Search | ~25 MB |

There is no background process, so idle RAM usage is effectively zero.

## Known Limits

- Text and Markdown only: `.txt` and `.md`
- No vector search
- No remote fetch
- No OCR, PDF parsing, HTML parsing, or binary indexing
- Search is simple substring matching, not full-text indexing

## Rollback

Delete the local registry:

```bash
rm -rf ~/.chub/
```

If you also want to remove the wrapper install:

```bash
rm -f ~/.local/bin/chub
rm -rf ~/.venvs/chub
```
