# Runbook

Use `chub` day to day with:

```bash
chub init
chub add ~/context-docs
chub list
chub search keyword
chub get <doc-id>
chub annotate <doc-id> "note"
chub annotate --list
chub stats
```

Local registry data lives at `~/.chub/`.

Store context documents under `~/context-docs/`, for example in `~/context-docs/skills/`, `~/context-docs/notes/`, and `~/context-docs/api/`, then re-run:

```bash
chub add ~/context-docs
```

Update the install with:

```bash
git pull && pip install -r requirements.txt
```

Check health with:

```bash
chub stats
```

Rollback local state with:

```bash
rm -rf ~/.chub/
```
