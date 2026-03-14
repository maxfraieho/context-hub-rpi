# Architecture

## Local-first vs remote-first

`context-hub-rpi` is local-first by design. It does not fetch remote content, call external APIs, or depend on a hosted service.

Why no network:

- Weak machines should not burn RAM and CPU on sync or background networking.
- Local docs are often enough for agent context on embedded boxes and small home servers.
- Offline operation matters on Raspberry Pi systems, lab machines, and private infra.
- A network-free tool is easier to audit and reason about.

This is the opposite of a remote-first system where indexing, syncing, or retrieval depends on a service boundary.

## Storage

The registry lives in:

- `~/.chub/index.json`
- `~/.chub/annotations.json`

Indexed files stay in place on the filesystem. `index.json` stores metadata such as:

- short ID
- absolute path
- title
- inferred tags
- added timestamp
- file size

`annotations.json` stores user notes keyed by document ID.

## Search

Search is pure Python grep-style scanning:

- title match: case-insensitive substring
- content match: case-insensitive substring over file lines
- context: one line before and one line after each hit

There is no FTS engine, no SQLite FTS, no embeddings, and no vector database.

This keeps the implementation small and predictable on low-memory hardware.

## ID Scheme

Document IDs are `sha256(absolute_path)[:8]`.

Properties:

- stable for a given absolute path
- cheap to compute
- short enough to type

Tradeoff:

- moving a file changes its ID because the absolute path changes

## Why `typer` + `rich` + `pathspec` only

- `typer`: minimal CLI definitions with clear argument parsing and help text
- `rich`: readable terminal tables and output without building a UI stack
- `pathspec`: `.gitignore`-style filtering when indexing directories

That dependency set is enough for the current scope. Anything heavier would push the project toward a larger runtime footprint without helping the core use case.
