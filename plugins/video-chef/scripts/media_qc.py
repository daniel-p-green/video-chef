#!/usr/bin/env python3
"""Run deterministic decode, black/freeze, and loudness checks on one media file."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--black-min-duration", type=float, default=1.0)
    parser.add_argument("--freeze-min-duration", type=float, default=2.0)
    return parser.parse_args()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def probe(path: Path) -> dict:
    completed = run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)
    ])
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    return json.loads(completed.stdout)


def black_events(log: str) -> list[dict]:
    pattern = re.compile(
        r"black_start:(?P<start>-?\d+(?:\.\d+)?)\s+black_end:(?P<end>-?\d+(?:\.\d+)?)\s+black_duration:(?P<duration>-?\d+(?:\.\d+)?)"
    )
    return [{key: float(value) for key, value in match.groupdict().items()} for match in pattern.finditer(log)]


def freeze_events(log: str) -> list[dict]:
    events: list[dict] = []
    current: dict = {}
    for line in log.splitlines():
        start = re.search(r"freeze_start:\s*(-?\d+(?:\.\d+)?)", line)
        duration = re.search(r"freeze_duration:\s*(-?\d+(?:\.\d+)?)", line)
        end = re.search(r"freeze_end:\s*(-?\d+(?:\.\d+)?)", line)
        if start:
            if current:
                events.append(current)
            current = {"start": float(start.group(1))}
        if duration:
            current["duration"] = float(duration.group(1))
        if end:
            current["end"] = float(end.group(1))
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


def last_number(pattern: str, text: str) -> float | None:
    values = re.findall(pattern, text, flags=re.MULTILINE)
    return float(values[-1]) if values else None


def loudness(log: str) -> dict:
    return {
        "integrated_lufs": last_number(r"^\s*I:\s*(-?\d+(?:\.\d+)?)\s+LUFS", log),
        "loudness_range_lu": last_number(r"^\s*LRA:\s*(-?\d+(?:\.\d+)?)\s+LU", log),
        "true_peak_dbfs": last_number(r"^\s*Peak:\s*(-?\d+(?:\.\d+)?)\s+dBFS", log),
    }


def markdown(report: dict) -> str:
    lines = [
        "# Media QC report", "", f"File: `{report['path']}`", f"Generated: {report['generated_utc']}", "",
        "## Decode", "", f"- Result: {'pass' if report['decode']['passed'] else 'fail'}",
    ]
    if report["decode"]["errors"]:
        lines.append(f"- Errors: `{report['decode']['errors']}`")
    if report.get("black_intervals") is not None:
        lines.extend(["", "## Black intervals", ""])
        lines.append(f"- Flagged: {len(report['black_intervals'])}")
        for event in report["black_intervals"]:
            lines.append(f"- {event['start']:.3f}s–{event['end']:.3f}s ({event['duration']:.3f}s)")
    if report.get("freeze_intervals") is not None:
        lines.extend(["", "## Frozen intervals", "", f"- Flagged: {len(report['freeze_intervals'])}"])
        for event in report["freeze_intervals"]:
            lines.append("- " + ", ".join(f"{key}={value:.3f}s" for key, value in event.items()))
    if report.get("loudness") is not None:
        audio = report["loudness"]
        lines.extend([
            "", "## Audio measurement", "",
            f"- Integrated: {audio['integrated_lufs']} LUFS",
            f"- Loudness range: {audio['loudness_range_lu']} LU",
            f"- True peak: {audio['true_peak_dbfs']} dBFS",
        ])
    lines.extend([
        "", "Detector findings require editorial interpretation. Automated checks do not replace full normal-speed picture and sound review.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("error: ffmpeg and ffprobe must be installed and on PATH", file=sys.stderr)
        return 2
    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"error: input does not exist: {source}", file=sys.stderr)
        return 2
    if args.black_min_duration < 0 or args.freeze_min_duration < 0:
        print("error: detector durations must be non-negative", file=sys.stderr)
        return 2

    try:
        metadata = probe(source)
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    streams = metadata.get("streams", [])
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)

    decoded = run([
        "ffmpeg", "-hide_banner", "-v", "error", "-i", str(source),
        "-map", "0:v?", "-map", "0:a?", "-f", "null", "-",
    ])
    report: dict = {
        "path": str(source),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": float(metadata.get("format", {}).get("duration", 0) or 0),
        "stream_count": len(streams),
        "decode": {"passed": decoded.returncode == 0, "errors": decoded.stderr.strip()},
        "black_intervals": None,
        "freeze_intervals": None,
        "loudness": None,
    }

    if has_video:
        black = run([
            "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(source),
            "-an", "-vf", f"blackdetect=d={args.black_min_duration}", "-f", "null", "-",
        ])
        freeze = run([
            "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(source),
            "-an", "-vf", f"freezedetect=n=-60dB:d={args.freeze_min_duration}", "-f", "null", "-",
        ])
        report["black_intervals"] = black_events(black.stderr)
        report["freeze_intervals"] = freeze_events(freeze.stderr)

    if has_audio:
        measured = run([
            "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(source),
            "-vn", "-filter_complex", "ebur128=peak=true", "-f", "null", "-",
        ])
        report["loudness"] = loudness(measured.stderr)

    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if report["decode"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
