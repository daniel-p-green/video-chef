#!/usr/bin/env python3
"""Detect video scene boundaries with FFmpeg and optionally extract boundary frames."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


PTS_RE = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, help="CSV or JSON manifest")
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--frames-dir", type=Path)
    parser.add_argument("--max-scenes", type=int, default=500)
    return parser.parse_args()


def duration(path: Path) -> float:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(json.loads(completed.stdout)["format"]["duration"])


def main() -> int:
    args = parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("error: ffmpeg and ffprobe are required", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    if not source.is_file() or not 0 < args.threshold < 1 or args.max_scenes < 1:
        print("error: valid input, 0 < threshold < 1, and max-scenes >= 1 are required", file=sys.stderr)
        return 2
    frames = args.frames_dir.expanduser().resolve() if args.frames_dir else None
    if frames and frames.exists() and any(frames.iterdir()):
        print(f"error: frames directory is not empty: {frames}", file=sys.stderr)
        return 2
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(source),
        "-filter:v", f"select='gt(scene,{args.threshold})',showinfo", "-an", "-f", "null", "-",
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        print(completed.stderr.strip() or "error: scene detection failed", file=sys.stderr)
        return 1
    boundaries = sorted({0.0, *(float(match.group(1)) for match in PTS_RE.finditer(completed.stderr))})
    if len(boundaries) > args.max_scenes:
        print(f"error: detected {len(boundaries)} boundaries, exceeding --max-scenes {args.max_scenes}", file=sys.stderr)
        return 1
    total = duration(source)
    rows = [
        {
            "scene": index + 1, "start": start,
            "end": boundaries[index + 1] if index + 1 < len(boundaries) else total,
            "duration": (boundaries[index + 1] if index + 1 < len(boundaries) else total) - start,
            "source": str(source),
        }
        for index, start in enumerate(boundaries)
    ]
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".json":
        output.write_text(json.dumps({"threshold": args.threshold, "scenes": rows}, indent=2) + "\n", encoding="utf-8")
    else:
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["scene", "start", "end", "duration", "source"])
            writer.writeheader()
            writer.writerows(rows)
    if args.frames_dir:
        frames.mkdir(parents=True, exist_ok=True)
        for row in rows:
            frame = frames / f"scene-{row['scene']:04d}-{row['start']:.3f}s.jpg"
            extract = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(row["start"]),
                "-i", str(source), "-frames:v", "1", "-q:v", "2", str(frame),
            ]
            result = subprocess.run(extract, capture_output=True, text=True)
            if result.returncode:
                print(result.stderr.strip() or f"error: could not extract {frame.name}", file=sys.stderr)
                return 1
    print(output)
    print(f"scenes: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
