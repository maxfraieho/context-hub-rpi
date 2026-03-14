# RPi 3B Constraints

## RAM Budget

A Raspberry Pi 3B with roughly 897 MB usable RAM leaves little room for waste.

Example steady-state memory pressure on a small Pi:

| Process | RAM |
| --- | ---: |
| `notebooklm-mcp` | 117 MB |
| `tailscaled` | 71 MB |
| `chub` idle | 0 MB |

`chub` only consumes memory while a command is running. There is no resident service.

## Why No Daemon

A daemon would likely cost around 30 MB permanently on this class of machine. That is the wrong tradeoff for a tool whose job is:

- scan files
- print matches
- exit

Avoiding a daemon keeps the idle footprint at zero and leaves memory available for the actual agent workload.

## Safe Usage

Recommended:

- index small directories first
- prefer text-heavy repos and note folders
- keep indexed content human-readable
- use `.gitignore` to exclude junk from recursive adds

## Avoid

- indexing `node_modules`
- indexing huge binary dumps
- indexing directories larger than 1 GB in one pass
- assuming this is a search engine for PDFs, media, or archives

The implementation only handles `.md` and `.txt`, so feeding it giant mixed-content trees wastes time even if many files are skipped.
