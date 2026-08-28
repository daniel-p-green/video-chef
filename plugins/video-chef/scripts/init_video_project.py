#!/usr/bin/env python3
"""Create a non-destructive professional Video Chef project workspace."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

FOLDERS = (
    "01_brief", "02_sources", "03_analysis", "04_editable_project", "05_proofs",
    "06_review_candidates", "07_masters", "08_delivery", "09_logs",
)

TEMPLATES = {
    "VIDEO_BRIEF.template.md": "01_brief",
    "EDIT_PLAN.template.md": "03_analysis",
    "SELECTS.template.csv": "03_analysis",
    "RIGHTS_LOG.template.csv": "03_analysis",
    "SCREEN_REVIEW.template.csv": "03_analysis",
    "SPEAKER_MAP.template.csv": "03_analysis",
    "AUDIO_POST.template.md": "09_logs",
    "CAPTION_QA.template.md": "09_logs",
    "DELIVERY_SPEC.template.md": "08_delivery",
    "DECISION_LOG.template.md": "09_logs",
    "CHANGE_LOG.template.md": "09_logs",
    "QA_REPORT.template.md": "09_logs",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    return parser.parse_args()


def main() -> int:
    target = parse_args().path.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        print(f"error: target exists and is not empty: {target}", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        (target / name).mkdir(exist_ok=True)
    assets = Path(__file__).resolve().parent.parent / "assets"
    for name, folder in TEMPLATES.items():
        source = assets / name
        if not source.is_file():
            print(f"error: missing bundled template: {source}", file=sys.stderr)
            return 1
        destination = target / folder / name.replace(".template", "")
        shutil.copy2(source, destination)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
