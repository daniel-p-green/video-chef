#!/usr/bin/env python3
"""Render an evenly sampled contact sheet from one video."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--width", type=int, default=480, help="Width of each thumbnail")
    return parser.parse_args()


def duration(path: Path) -> float:
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    value = float(json.loads(completed.stdout)["format"]["duration"])
    if value <= 0:
        raise ValueError("video duration must be positive")
    return value


def main() -> int:
    args = parse_args()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("error: ffmpeg and ffprobe must be installed and on PATH", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"error: input does not exist: {source}", file=sys.stderr)
        return 2
    if args.frames < 2 or args.columns < 1 or args.width < 64:
        print("error: frames >= 2, columns >= 1, and width >= 64 are required", file=sys.stderr)
        return 2

    try:
        seconds = duration(source)
    except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: could not determine video duration: {exc}", file=sys.stderr)
        return 1

    rows = math.ceil(args.frames / args.columns)
    interval = seconds / args.frames
    # Offset by half an interval to avoid sampling slates or a terminal black frame.
    vf = (
        f"fps=1/{interval},trim=start={interval / 2}:end={seconds},"
        f"scale={args.width}:-2,"
        f"tile={args.columns}x{rows}:nb_frames={args.frames}:padding=6:margin=6"
    )
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
        "-vf", vf, "-frames:v", "1", str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        print(completed.stderr.strip() or "error: ffmpeg failed", file=sys.stderr)
        return completed.returncode
    samples = [interval * (index + 0.5) for index in range(args.frames)]
    print(output)
    print("sample times (seconds): " + ", ".join(f"{value:.3f}" for value in samples))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
