# Design Decisions

## Why Python, not Node.js

The original `context-hub` direction is Node.js-based. This project is not.

Python was chosen because:

- Python is already common on Raspberry Pi systems
- startup cost and operational complexity stay low
- the feature set fits standard-library-heavy code
- no JS toolchain is required just to index a few local files

## Why Filesystem-first, not a DB

The source of truth is the existing filesystem. `chub` stores metadata, not file copies.

Benefits:

- no content duplication
- easy rollback with `rm -rf ~/.chub/`
- easy inspection of stored state
- fewer moving parts than a database-backed design

## Why Grep, not Vector Search

On machines with less than 1 GB RAM, embeddings and vector indexes are usually the wrong default.

Simple substring search wins here because it is:

- cheap
- transparent
- deterministic
- good enough for small local corpora

If the target corpus is mostly your own notes, docs, and small repos, grep-style retrieval is often the highest-value per MB.

## Why CLI-first, not Web UI

A web UI adds background processes, packaging overhead, and a larger maintenance surface.

The CLI is the correct primary interface because:

- it works over SSH
- it composes with shell tools
- it keeps the runtime footprint small
- agents can call it directly

## Why Useful for Claude and Codex

`chub get <id>` prints document content directly to stdout with no wrapper format.

That makes it easy to:

- pipe content into an agent prompt
- capture output in scripts
- keep context retrieval explicit and inspectable

For agent workflows on weak hardware, a small local CLI is often more useful than a heavier interactive app.
