#!/usr/bin/env python3
"""Check SRT or WebVTT timing, overlap, line count, line length, and reading speed."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Cue:
    index: int
    start: float
    end: float
    lines: list[str]


def parse_time(value: str) -> float:
    match = re.fullmatch(r"(?:(\d+):)?(\d{2}):(\d{2})[,.](\d{3})", value.strip())
    if not match:
        raise ValueError(f"invalid timestamp: {value}")
    hours = int(match.group(1) or 0)
    return hours * 3600 + int(match.group(2)) * 60 + int(match.group(3)) + int(match.group(4)) / 1000


def parse(path: Path) -> list[Cue]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines()]
        if not lines or lines[0].strip() == "WEBVTT" or lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start_raw, end_raw = [part.strip().split()[0] for part in lines[timing_index].split("-->", 1)]
        cues.append(Cue(len(cues) + 1, parse_time(start_raw), parse_time(end_raw), lines[timing_index + 1 :]))
    if not cues:
        raise ValueError("no subtitle cues found")
    return cues


def visible_text(lines: list[str]) -> str:
    return re.sub(r"<[^>]+>", "", " ".join(lines)).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--max-lines", type=int, default=2)
    parser.add_argument("--max-chars-per-line", type=int, default=42)
    parser.add_argument("--max-cps", type=float, default=20.0)
    parser.add_argument("--min-duration", type=float, default=0.5)
    parser.add_argument("--max-duration", type=float, default=7.0)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-issues", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"error: input does not exist: {source}", file=sys.stderr)
        return 2
    try:
        cues = parse(source)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    issues: list[dict] = []
    previous: Cue | None = None
    for cue in cues:
        duration = cue.end - cue.start
        if duration <= 0:
            issues.append({"cue": cue.index, "type": "nonpositive-duration", "value": duration})
        elif duration < args.min_duration:
            issues.append({"cue": cue.index, "type": "short-duration", "value": duration})
        elif duration > args.max_duration:
            issues.append({"cue": cue.index, "type": "long-duration", "value": duration})
        if previous and cue.start < previous.end:
            issues.append({"cue": cue.index, "type": "overlap", "value": previous.end - cue.start})
        if len(cue.lines) > args.max_lines:
            issues.append({"cue": cue.index, "type": "too-many-lines", "value": len(cue.lines)})
        for line_number, line in enumerate(cue.lines, 1):
            length = len(visible_text([line]))
            if length > args.max_chars_per_line:
                issues.append({"cue": cue.index, "type": "long-line", "line": line_number, "value": length})
        chars = len(visible_text(cue.lines))
        cps = chars / duration if duration > 0 else float("inf")
        if cps > args.max_cps:
            issues.append({"cue": cue.index, "type": "high-reading-speed", "value": round(cps, 2)})
        if not visible_text(cue.lines):
            issues.append({"cue": cue.index, "type": "empty-text", "value": 0})
        previous = cue

    report = {
        "path": str(source),
        "cue_count": len(cues),
        "start_seconds": cues[0].start,
        "end_seconds": cues[-1].end,
        "thresholds": {
            "max_lines": args.max_lines,
            "max_chars_per_line": args.max_chars_per_line,
            "max_cps": args.max_cps,
            "min_duration": args.min_duration,
            "max_duration": args.max_duration,
        },
        "issues": issues,
        "cues": [asdict(cue) for cue in cues],
    }
    if args.format == "json":
        rendered = json.dumps(report, indent=2) + "\n"
    else:
        lines = [
            "# Subtitle QC report", "", f"File: `{source}`", f"Cues: {len(cues)}", f"Issues: {len(issues)}", "",
        ]
        lines.extend(
            f"- Cue {issue['cue']}: {issue['type']} ({issue['value']})" for issue in issues
        )
        lines.extend(["", "Automated readability checks do not replace human review over the actual picture."])
        rendered = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 1 if args.fail_on_issues and issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
