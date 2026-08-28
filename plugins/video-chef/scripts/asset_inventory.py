#!/usr/bin/env python3
"""Inventory every production asset, including non-media files and likely roles."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


EXTENSION_KINDS = {
    "video": {".3gp", ".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mts", ".mxf", ".webm", ".wmv"},
    "audio": {".aac", ".aif", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav"},
    "graphic": {".ai", ".eps", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".psd", ".svg", ".tif", ".tiff", ".webp"},
    "caption": {".ass", ".scc", ".srt", ".stl", ".ttml", ".vtt"},
    "document": {".csv", ".doc", ".docx", ".json", ".md", ".pdf", ".rtf", ".txt", ".xls", ".xlsx", ".yaml", ".yml"},
    "project": {".aep", ".aepx", ".mogrt", ".prproj", ".sesx"},
    "font": {".otf", ".ttc", ".ttf", ".woff", ".woff2"},
    "archive": {".7z", ".gz", ".rar", ".tar", ".zip"},
}

ROLE_TERMS = (
    ("screen-recording", {"screen", "screencast", "demo", "capture"}),
    ("camera", {"camera", "cam", "angle", "take"}),
    ("dialogue", {"dialogue", "interview", "lav", "boom", "voice", "vo"}),
    ("music", {"music", "score", "song"}),
    ("sound-effect", {"sfx", "sound-effect", "sound_effect"}),
    ("brand", {"brand", "styleguide", "style-guide", "guidelines"}),
    ("graphic", {"graphic", "logo", "title", "lower-third", "lower_third", "mogrt"}),
    ("script", {"script", "copy", "transcript"}),
    ("caption", {"caption", "subtitle"}),
    ("project", {"project", "premiere", "after-effects", "after_effects"}),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--format", choices=("csv", "json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--hash", choices=("sha256",))
    return parser.parse_args()


def discover(inputs: list[Path], include_hidden: bool) -> list[Path]:
    files: set[Path] = set()
    for raw in inputs:
        path = raw.expanduser().resolve()
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if not candidate.is_file():
                    continue
                relative = candidate.relative_to(path)
                if not include_hidden and any(part.startswith(".") for part in relative.parts):
                    continue
                files.add(candidate.resolve())
        else:
            print(f"warning: skipped missing input: {raw}", file=sys.stderr)
    return sorted(files, key=lambda item: str(item).lower())


def kind_for(path: Path) -> str:
    suffix = path.suffix.lower()
    return next((kind for kind, extensions in EXTENSION_KINDS.items() if suffix in extensions), "other")


def role_for(path: Path, kind: str) -> str:
    tokens = {token for part in path.parts for token in part.lower().replace(" ", "-").split("-")}
    joined = str(path).lower()
    for role, terms in ROLE_TERMS:
        if any(term in tokens or term in joined for term in terms):
            return role
    return kind


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record(path: Path, hash_algorithm: str | None) -> dict:
    stat = path.stat()
    kind = kind_for(path)
    item = {
        "path": str(path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "kind": kind,
        "likely_role": role_for(path, kind),
        "bytes": stat.st_size,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }
    if hash_algorithm:
        item[hash_algorithm] = hash_file(path, hash_algorithm)
    return item


def render_markdown(report: dict) -> str:
    lines = [
        "# Production asset inventory", "", f"Generated: {report['generated_utc']}",
        f"Files: {len(report['files'])}", "",
        "| File | Kind | Likely role | Bytes |", "|---|---|---|---:|",
    ]
    for item in report["files"]:
        lines.append(f"| `{item['path']}` | {item['kind']} | {item['likely_role']} | {item['bytes']} |")
    lines.extend(["", "Role labels are heuristics; confirm file purpose, approval, rights, and canonical status before editing."])
    return "\n".join(lines) + "\n"


def render_csv(report: dict) -> str:
    from io import StringIO

    output = StringIO()
    fields = ["path", "name", "extension", "kind", "likely_role", "bytes", "modified_utc"]
    if report["hash_algorithm"]:
        fields.append(report["hash_algorithm"])
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(report["files"])
    return output.getvalue()


def main() -> int:
    args = parse_args()
    output_path = args.output.expanduser().resolve() if args.output else None
    paths = [path for path in discover(args.inputs, args.include_hidden) if path != output_path]
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": args.hash,
        "files": [record(path, args.hash) for path in paths],
    }
    if args.format == "json":
        rendered = json.dumps(report, indent=2) + "\n"
    elif args.format == "csv":
        rendered = render_csv(report)
    else:
        rendered = render_markdown(report)
    if args.output:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
