# API Notes

## Auth

- Tokens are local-only for development.
- Rotate tokens manually after changing test fixtures.

## Retrieval

- Use `chub search auth` to find these notes quickly.
- Use `chub get <id>` when an agent needs the full document body.

## Constraints

- Keep responses text-first for low-RAM machines.
- Avoid adding binary payload examples to the local registry.
