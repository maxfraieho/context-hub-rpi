#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pathspec
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False, help="Local-first context registry CLI.")
console = Console(stderr=False)
error_console = Console(stderr=True)

CHUB_DIR = Path.home() / ".chub"
INDEX_PATH = CHUB_DIR / "index.json"
ANNOTATIONS_PATH = CHUB_DIR / "annotations.json"
SUPPORTED_SUFFIXES = {".md", ".txt"}
CONTEXT_LINES = 1


@dataclass
class IndexedDoc:
    id: str
    path: str
    title: str
    tags: list[str]
    added_at: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "tags": self.tags,
            "added_at": self.added_at,
            "size_bytes": self.size_bytes,
        }


def ensure_store() -> None:
    CHUB_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        write_json(INDEX_PATH, [])
    if not ANNOTATIONS_PATH.exists():
        write_json(ANNOTATIONS_PATH, {})


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_index() -> list[IndexedDoc]:
    ensure_store()
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    docs: list[IndexedDoc] = []
    for item in raw:
        docs.append(
            IndexedDoc(
                id=item["id"],
                path=item["path"],
                title=item["title"],
                tags=list(item.get("tags", [])),
                added_at=item["added_at"],
                size_bytes=int(item["size_bytes"]),
            )
        )
    return docs


def save_index(docs: list[IndexedDoc]) -> None:
    write_json(INDEX_PATH, [doc.to_dict() for doc in docs])


def load_annotations() -> dict[str, list[str]]:
    ensure_store()
    raw = json.loads(ANNOTATIONS_PATH.read_text(encoding="utf-8"))
    return {key: list(value) for key, value in raw.items()}


def save_annotations(annotations: dict[str, list[str]]) -> None:
    write_json(ANNOTATIONS_PATH, annotations)


def short_id_for(path: Path) -> str:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()
    return digest[:8]


def file_title(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    return text.lstrip("#").strip() or path.stem
    except OSError:
        return path.stem
    return path.stem


def detect_tags(path: Path) -> list[str]:
    parent = path.parent.name.strip()
    return [parent] if parent else []


def build_doc(path: Path) -> IndexedDoc:
    stat = path.stat()
    return IndexedDoc(
        id=short_id_for(path),
        path=str(path),
        title=file_title(path),
        tags=detect_tags(path),
        added_at=datetime.now(timezone.utc).isoformat(),
        size_bytes=stat.st_size,
    )


def load_gitignore_spec(root: Path) -> pathspec.PathSpec | None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None
    patterns = gitignore.read_text(encoding="utf-8").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def iter_candidate_files(target: Path) -> list[Path]:
    resolved = target.expanduser().resolve()
    if not resolved.exists():
        raise typer.BadParameter(f"Path does not exist: {target}")

    if resolved.is_file():
        if resolved.suffix.lower() in SUPPORTED_SUFFIXES:
            return [resolved]
        return []

    spec = load_gitignore_spec(resolved)
    files: list[Path] = []
    for path in resolved.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if spec is not None:
            relative = path.relative_to(resolved).as_posix()
            if spec.match_file(relative):
                continue
        files.append(path.resolve())
    return sorted(files)


def get_doc_by_id(doc_id: str, docs: list[IndexedDoc]) -> IndexedDoc:
    for doc in docs:
        if doc.id == doc_id:
            return doc
    raise typer.BadParameter(f"Unknown document id: {doc_id}")


def emit_text(text: str) -> None:
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")


def print_error(message: str, code: int = 1) -> None:
    error_console.print(message)
    raise typer.Exit(code)


@app.command()
def init() -> None:
    """Create ~/.chub/."""
    ensure_store()
    console.print(f"Initialized context registry at {CHUB_DIR}", markup=False)


@app.command()
def add(path: str) -> None:
    """Add a file or directory of markdown/text files."""
    docs = load_index()
    known_paths = {doc.path for doc in docs}
    known_ids = {doc.id for doc in docs}
    candidates = iter_candidate_files(Path(path))

    added = 0
    skipped = 0
    for candidate in candidates:
        candidate_str = str(candidate)
        candidate_id = short_id_for(candidate)
        if candidate_str in known_paths or candidate_id in known_ids:
            skipped += 1
            continue
        doc = build_doc(candidate)
        docs.append(doc)
        known_paths.add(doc.path)
        known_ids.add(doc.id)
        added += 1

    save_index(sorted(docs, key=lambda doc: doc.added_at))
    console.print(f"Added {added} document(s); skipped {skipped} already indexed.", markup=False)


@app.command("list")
def list_docs() -> None:
    """List indexed documents."""
    docs = load_index()
    table = Table(show_header=True, header_style="bold")
    table.add_column("id", no_wrap=True)
    table.add_column("title")
    table.add_column("path")
    table.add_column("tags")

    for doc in docs:
        table.add_row(doc.id, doc.title, doc.path, ",".join(doc.tags))
    console.print(table, markup=False)


def match_title(doc: IndexedDoc, query: str) -> bool:
    return query.lower() in doc.title.lower()


def search_file(path: Path, query: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return matches

    lowered = query.lower()
    seen: set[int] = set()
    for idx, line in enumerate(lines):
        if lowered not in line.lower():
            continue
        start = max(0, idx - CONTEXT_LINES)
        end = min(len(lines), idx + CONTEXT_LINES + 1)
        for context_idx in range(start, end):
            if context_idx in seen:
                continue
            seen.add(context_idx)
            matches.append((context_idx + 1, lines[context_idx]))
    return matches


@app.command()
def search(q: str) -> None:
    """Search document titles and file content."""
    docs = load_index()
    any_match = False
    for doc in docs:
        title_hit = match_title(doc, q)
        content_hits = search_file(Path(doc.path), q)
        if not title_hit and not content_hits:
            continue

        any_match = True
        console.print(f"[{doc.id}] {doc.title} :: {doc.path}", markup=False)
        if title_hit:
            console.print("title match", markup=False)
        for line_no, line in content_hits:
            console.print(f"{line_no}: {line}", markup=False)
        console.print(markup=False)

    if not any_match:
        raise typer.Exit(1)


@app.command()
def get(doc_id: str) -> None:
    """Print document content to stdout."""
    docs = load_index()
    doc = get_doc_by_id(doc_id, docs)
    path = Path(doc.path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print_error(f"Failed to read {path}: {exc}")
    emit_text(text)


@app.command()
def annotate(
    doc_id: str | None = typer.Argument(default=None),
    note: str | None = typer.Argument(default=None),
    list_annotations: bool = typer.Option(False, "--list", help="Print all annotations."),
) -> None:
    """Append or list annotations."""
    annotations = load_annotations()
    if list_annotations:
        if not annotations:
            console.print("No annotations.", markup=False)
            return
        docs = {doc.id: doc for doc in load_index()}
        for current_id in sorted(annotations):
            title = docs[current_id].title if current_id in docs else "<missing>"
            console.print(f"[{current_id}] {title}", markup=False)
            for entry in annotations[current_id]:
                console.print(f"- {entry}", markup=False)
            console.print(markup=False)
        return

    if doc_id is None or note is None:
        raise typer.BadParameter("annotate requires <id> and <note>, or use --list")

    get_doc_by_id(doc_id, load_index())
    annotations.setdefault(doc_id, []).append(note)
    save_annotations(annotations)
    console.print(f"Annotated {doc_id}", markup=False)


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{int(size_bytes)} B"


@app.command()
def stats() -> None:
    """Show registry stats."""
    docs = load_index()
    annotations = load_annotations()
    annotation_count = sum(len(items) for items in annotations.values())
    total_size = sum(doc.size_bytes for doc in docs)
    console.print(f"total docs: {len(docs)}", markup=False)
    console.print(f"total size: {format_size(total_size)}", markup=False)
    console.print(f"annotation count: {annotation_count}", markup=False)
    console.print(f"path: {CHUB_DIR}", markup=False)


def main() -> None:
    try:
        app()
    except typer.BadParameter as exc:
        print_error(str(exc))


if __name__ == "__main__":
    main()
