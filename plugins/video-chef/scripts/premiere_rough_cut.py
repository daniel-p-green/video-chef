#!/usr/bin/env python3
"""Build and validate a source-linked, non-mutating Premiere rough-cut plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED = {"source_path", "source_in", "source_out", "story_order"}


def plan_digest(plan: dict[str, Any]) -> str:
    digest_payload = {key: value for key, value in plan.items() if key not in {"created_at", "plan_sha256"}}
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def build_plan(rows: list[dict[str, str]], target: str, fps: float, base_dir: Path) -> dict[str, Any]:
    if not target or target.strip() != target:
        raise ValueError("target sequence name must be non-empty without surrounding whitespace")
    if not target.startswith("VC_ROUGH_CUT_"):
        raise ValueError("target sequence must start with VC_ROUGH_CUT_ to prove isolation")
    if fps <= 0:
        raise ValueError("fps must be positive")
    segments: list[dict[str, Any]] = []
    seen_orders: set[int] = set()
    for line, row in enumerate(rows, start=2):
        try:
            order = int(row["story_order"])
            source_in = float(row["source_in"])
            source_out = float(row["source_out"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"line {line}: invalid numeric field") from exc
        raw_source = Path(row["source_path"]).expanduser()
        resolved_source = raw_source if raw_source.is_absolute() else base_dir / raw_source
        resolved_source = resolved_source.resolve()
        source_path = str(resolved_source)
        if order < 1 or order in seen_orders:
            raise ValueError(f"line {line}: story_order must be unique and positive")
        if source_in < 0 or source_out <= source_in:
            raise ValueError(f"line {line}: source_out must be greater than source_in")
        seen_orders.add(order)
        segments.append({
            "story_order": order,
            "source_path": source_path,
            "source_exists": resolved_source.is_file(),
            "source_in_seconds": round(source_in, 6),
            "source_out_seconds": round(source_out, 6),
            "duration_seconds": round(source_out - source_in, 6),
            "speaker": row.get("speaker", "").strip(),
            "transcript": row.get("transcript", "").strip(),
            "reason": row.get("reason", "").strip(),
        })
    segments.sort(key=lambda item: item["story_order"])
    cursor = 0.0
    for segment in segments:
        segment["timeline_in_seconds"] = round(cursor, 6)
        cursor += segment["duration_seconds"]
        segment["timeline_out_seconds"] = round(cursor, 6)
    plan: dict[str, Any] = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "plan_only",
        "target_sequence": target,
        "target_sequence_policy": "new_isolated_sequence_only",
        "fps": fps,
        "duration_seconds": round(cursor, 6),
        "segments": segments,
        "execution": {
            "requested": False,
            "supported_by_bundled_connector": False,
            "reason": "Bundled UXP connector 1.1 is read-only; review and approve this plan before any future write-capable connector is used.",
        },
    }
    plan["plan_sha256"] = plan_digest(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if plan.get("mode") != "plan_only":
        issues.append("mode must remain plan_only")
    if plan.get("target_sequence_policy") != "new_isolated_sequence_only":
        issues.append("target sequence policy must require isolation")
    if not str(plan.get("target_sequence", "")).startswith("VC_ROUGH_CUT_"):
        issues.append("target sequence name is not isolated")
    if plan.get("execution", {}).get("requested") is not False:
        issues.append("execution.requested must be false")
    if plan.get("plan_sha256") != plan_digest(plan):
        issues.append("plan_sha256 does not match the plan contents")
    previous = 0.0
    for index, segment in enumerate(plan.get("segments", []), start=1):
        if float(segment.get("timeline_in_seconds", -1)) != previous:
            issues.append(f"segment {index} does not start at the prior segment boundary")
        previous = float(segment.get("timeline_out_seconds", -1))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selects", type=Path, help="CSV with source_path, source_in, source_out, and story_order")
    parser.add_argument("output", type=Path)
    parser.add_argument("--target-sequence", required=True)
    parser.add_argument("--fps", type=float, default=29.97)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate_only:
            plan = json.loads(args.selects.read_text(encoding="utf-8"))
        else:
            plan = build_plan(read_rows(args.selects), args.target_sequence, args.fps, args.selects.parent.resolve())
        issues = validate_plan(plan)
        if issues:
            raise ValueError("; ".join(issues))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote guarded plan {args.output} ({len(plan.get('segments', []))} segments)")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
