#!/usr/bin/env python3
"""Extract a bounded, timestamped frame sequence for close visual or motion analysis."""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--fps", type=float, default=12.0)
    parser.add_argument("--max-frames", type=int, default=300)
    parser.add_argument("--width", type=int, default=960)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which("ffmpeg"):
        print("error: ffmpeg is required", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    span = args.end - args.start
    expected = math.ceil(span * args.fps)
    if not source.is_file() or args.start < 0 or span <= 0 or args.fps <= 0 or args.width < 64:
        print("error: valid input, non-negative start, end > start, fps > 0, and width >= 64 are required", file=sys.stderr)
        return 2
    if expected > args.max_frames:
        print(f"error: requested about {expected} frames, exceeding --max-frames {args.max_frames}", file=sys.stderr)
        return 2
    output = args.output_dir.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        print(f"error: output directory is not empty: {output}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    pattern = output / "frame-%06d.jpg"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(args.start),
        "-i", str(source), "-t", str(span), "-vf", f"fps={args.fps},scale={args.width}:-2",
        "-q:v", "2", str(pattern),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        print(completed.stderr.strip() or "error: frame extraction failed", file=sys.stderr)
        return completed.returncode
    frames = sorted(output.glob("frame-*.jpg"))
    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame", "time_seconds", "source"])
        writer.writeheader()
        for index, frame in enumerate(frames):
            writer.writerow({"frame": frame.name, "time_seconds": args.start + index / args.fps, "source": str(source)})
    print(output)
    print(f"frames: {len(frames)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
