#!/usr/bin/env python3
"""Create a reproducible ffprobe inventory for local media files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

MEDIA_EXTENSIONS = {
    ".3gp", ".aac", ".aif", ".aiff", ".avi", ".flac", ".m4a", ".m4v",
    ".mkv", ".mov", ".mp3", ".mp4", ".mts", ".mxf", ".ogg", ".ogv",
    ".wav", ".webm", ".wmv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Files or directories to inspect")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write to this file instead of stdout")
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--hash", choices=("sha256",), help="Add a content hash for exact file identity")
    return parser.parse_args()


def discover(inputs: list[Path], include_hidden: bool) -> list[Path]:
    found: set[Path] = set()
    for raw in inputs:
        path = raw.expanduser().resolve()
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS:
            found.add(path)
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if not candidate.is_file() or candidate.suffix.lower() not in MEDIA_EXTENSIONS:
                    continue
                if not include_hidden and any(part.startswith(".") for part in candidate.relative_to(path).parts):
                    continue
                found.add(candidate.resolve())
        else:
            print(f"warning: skipped missing or unsupported input: {raw}", file=sys.stderr)
    return sorted(found, key=lambda item: str(item).lower())


def rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path, hash_algorithm: str | None = None) -> dict:
    command = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    base = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }
    if hash_algorithm:
        base[f"{hash_algorithm}"] = file_hash(path, hash_algorithm)
    if completed.returncode:
        return {**base, "status": "error", "error": completed.stderr.strip() or "ffprobe failed"}

    raw = json.loads(completed.stdout)
    streams = raw.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    duration = raw.get("format", {}).get("duration")
    return {
        **base,
        "status": "ok",
        "duration_seconds": float(duration) if duration not in (None, "N/A") else None,
        "format": raw.get("format", {}).get("format_name"),
        "video": None if video is None else {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "pixel_format": video.get("pix_fmt"),
            "average_fps": rate(video.get("avg_frame_rate")),
            "source_fps": video.get("r_frame_rate"),
            "rotation": (video.get("tags") or {}).get("rotate"),
        },
        "audio": [
            {
                "codec": item.get("codec_name"),
                "sample_rate": int(item["sample_rate"]) if item.get("sample_rate", "").isdigit() else None,
                "channels": item.get("channels"),
                "layout": item.get("channel_layout"),
                "language": (item.get("tags") or {}).get("language"),
            }
            for item in audio
        ],
        "stream_count": len(streams),
    }


def duration_text(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{secs:06.3f}"


def markdown(report: dict) -> str:
    lines = [
        "# Media inventory",
        "",
        f"Generated: {report['generated_utc']}",
        f"Files: {len(report['files'])}",
        "",
        "| File | Duration | Picture | FPS | Video codec | Audio | Status |",
        "|---|---:|---|---:|---|---|---|",
    ]
    for item in report["files"]:
        if item["status"] != "ok":
            lines.append(f"| `{item['path']}` | — | — | — | — | — | error: {item['error']} |")
            continue
        video = item["video"] or {}
        picture = f"{video.get('width')}×{video.get('height')}" if video else "audio only"
        fps = f"{video.get('average_fps'):.3f}" if video.get("average_fps") is not None else "—"
        audio = ", ".join(
            f"{stream.get('codec') or '?'} {stream.get('sample_rate') or '?'} Hz {stream.get('layout') or stream.get('channels') or '?'}"
            for stream in item["audio"]
        ) or "none"
        lines.append(
            f"| `{item['path']}` | {duration_text(item['duration_seconds'])} | {picture} | {fps} | "
            f"{video.get('codec') or 'none'} | {audio} | ok |"
        )
    lines.extend(["", "Technical inventory only; inspect picture and sound before editorial decisions."])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    if shutil.which("ffprobe") is None:
        print("error: ffprobe is not installed or not on PATH", file=sys.stderr)
        return 2
    files = discover(args.inputs, args.include_hidden)
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": args.hash,
        "files": [probe(path, args.hash) for path in files],
    }
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 1 if any(item["status"] == "error" for item in report["files"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
