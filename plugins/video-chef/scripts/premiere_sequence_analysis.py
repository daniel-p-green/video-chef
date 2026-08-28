#!/usr/bin/env python3
"""Validate a Video Chef Premiere snapshot and write a narrative evidence report."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any


def unwrap_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    if "schema_version" in value:
        return value
    result = value.get("result")
    if not isinstance(result, dict):
        raise ValueError("input is neither a snapshot nor a broker response envelope")
    if result.get("ok") is not True:
        raise ValueError(f"bridge request failed: {result.get('error', 'unknown error')}")
    snapshot = result.get("data")
    if not isinstance(snapshot, dict):
        raise ValueError("bridge response envelope is missing result.data")
    return snapshot


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        staged.write_text(content, encoding="utf-8")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def validate(snapshot: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if snapshot.get("schema_version") not in {"1.0", "1.1"}:
        issues.append("schema_version must be 1.0 or 1.1")
    for key in ("captured_at", "project", "sequence", "tracks"):
        if key not in snapshot:
            issues.append(f"missing {key}")
    sequence = snapshot.get("sequence", {})
    if not isinstance(sequence, dict) or not sequence.get("name"):
        issues.append("sequence.name is required")
    tracks = snapshot.get("tracks")
    if not isinstance(tracks, list):
        issues.append("tracks must be a list")
        return issues
    for track_index, track in enumerate(tracks):
        if not isinstance(track, dict) or track.get("media_type") not in {"video", "audio"}:
            issues.append(f"track {track_index} has invalid media_type")
            continue
        items = track.get("items")
        if not isinstance(items, list):
            issues.append(f"track {track_index} items must be a list")
            continue
        previous_start = -1.0
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                issues.append(f"track {track_index} item {item_index} must be an object")
                continue
            try:
                start = float(item["timeline_start_seconds"])
                end = float(item["timeline_end_seconds"])
                source_in = float(item["source_in_seconds"])
                source_out = float(item["source_out_seconds"])
            except (KeyError, TypeError, ValueError):
                issues.append(f"track {track_index} item {item_index} has invalid timing")
                continue
            if start < 0 or end <= start or source_in < 0 or source_out <= source_in:
                issues.append(f"track {track_index} item {item_index} has non-positive timing")
            if start < previous_start:
                issues.append(f"track {track_index} items are not timeline ordered")
            previous_start = start
    return issues


def report(snapshot: dict[str, Any]) -> str:
    sequence = snapshot["sequence"]
    tracks = snapshot["tracks"]
    video = [track for track in tracks if track["media_type"] == "video"]
    audio = [track for track in tracks if track["media_type"] == "audio"]
    video_items = [item for track in video for item in track["items"]]
    audio_items = [item for track in audio for item in track["items"]]
    all_items = video_items + audio_items
    unique_sources = sorted({item.get("media_path") or item.get("project_item_name", "unknown") for item in all_items})
    disabled = sum(bool(item.get("disabled")) for item in all_items)
    lines = [
        "# Premiere sequence evidence report",
        "",
        f"- Captured: `{snapshot['captured_at']}`",
        f"- Project: `{snapshot['project'].get('name', 'unknown')}`",
        f"- Sequence: `{sequence['name']}`",
        f"- Duration: `{float(sequence.get('duration_seconds', 0)):.3f}s`",
        f"- Frame size: `{sequence.get('frame_width', '?')}x{sequence.get('frame_height', '?')}`",
        f"- Tracks: `{len(video)} video / {len(audio)} audio`",
        f"- Clip instances: `{len(video_items)} video / {len(audio_items)} audio`",
        f"- Unique sources: `{len(unique_sources)}`",
        f"- Disabled clip instances: `{disabled}`",
    ]
    inspection_issues = snapshot.get("issues", [])
    if snapshot.get("partial") or inspection_issues:
        lines.extend([
            f"- Snapshot completeness: `partial` ({len(inspection_issues)} inspection issue(s))",
            "",
            "## Snapshot warnings",
            "",
        ])
        for issue in inspection_issues:
            lines.append(f"- `{issue.get('scope', 'unknown')}`: {issue.get('error', 'inspection failed')}")
    else:
        lines.append("- Snapshot completeness: `complete for declared fields`")
    lines.extend(["", "## Timeline evidence", ""])
    for track in tracks:
        lines.append(f"### {track.get('name') or track['media_type'].title()} {int(track.get('index', 0)) + 1}")
        lines.append("")
        if not track["items"]:
            lines.append("_No clip items._")
        for item in track["items"]:
            lines.append(
                f"- `{item['timeline_start_seconds']:.3f}-{item['timeline_end_seconds']:.3f}` "
                f"{item.get('name', 'Unnamed')} — source `{item['source_in_seconds']:.3f}-{item['source_out_seconds']:.3f}`"
            )
        lines.append("")
    lines.extend([
        "## Editorial interpretation boundary",
        "",
        "This snapshot proves timeline structure and source ranges only. Narrative intent, performance quality, visual continuity, mix quality, and owner approval require transcript, frame, sound-on, and human review evidence.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--validated-json", type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.snapshot.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("snapshot root must be an object")
        snapshot = unwrap_snapshot(value)
        issues = validate(snapshot)
        if issues:
            raise ValueError("; ".join(issues))
        write_text_atomic(args.output, report(snapshot))
        if args.validated_json:
            write_text_atomic(args.validated_json, json.dumps(snapshot, indent=2) + "\n")
        print(f"Wrote {args.output}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
