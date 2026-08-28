#!/usr/bin/env python3
"""Create readable, word-timed, speaker-aware transcript records and flag production cues."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_CUES = (
    "that was perfect", "good take", "great take", "use that", "one more",
    "do it again", "start over", "pick it up", "reset", "cut",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Whisper JSON or local audio/video file")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--engine", choices=("auto", "json", "whisper", "mlx-whisper"), default="auto")
    parser.add_argument("--model", help="Explicit local Whisper model name/path; may download if the engine cannot find it")
    parser.add_argument("--language")
    parser.add_argument("--speaker-map", type=Path, help="CSV with start,end,speaker from a diarization pass")
    parser.add_argument("--cue", action="append", default=[], help="Additional production cue phrase")
    return parser.parse_args()


def run_engine(source: Path, engine: str, model: str | None, language: str | None) -> tuple[dict, dict]:
    if engine == "auto":
        engine = "json" if source.suffix.lower() == ".json" else "whisper"
    if engine == "json":
        return json.loads(source.read_text(encoding="utf-8")), {"engine": "json", "model": None}
    executable = shutil.which("whisper" if engine == "whisper" else "mlx_whisper")
    if not executable:
        raise RuntimeError(f"{engine} is not installed; provide Whisper JSON or install the selected local engine")
    if not model:
        raise RuntimeError("--model is required for media transcription so model selection/download is explicit")
    with tempfile.TemporaryDirectory(prefix="video-chef-transcript-") as temp:
        if engine == "whisper":
            command = [
                executable, str(source), "--output_dir", temp, "--output_format", "json",
                "--word_timestamps", "True", "--model", model, "--verbose", "False",
            ]
        else:
            command = [
                executable, str(source), "--output-dir", temp, "--output-format", "json",
                "--word-timestamps", "True", "--model", model, "--verbose", "False",
            ]
        if language:
            command += ["--language", language]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"{engine} failed")
        candidates = list(Path(temp).glob("*.json"))
        if len(candidates) != 1:
            raise RuntimeError(f"expected one transcript JSON, found {len(candidates)}")
        return json.loads(candidates[0].read_text(encoding="utf-8")), {"engine": engine, "model": model}


def read_speaker_map(path: Path | None) -> list[dict]:
    if path is None:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {"start", "end", "speaker"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("speaker map must contain start,end,speaker columns")
    return [{"start": float(row["start"]), "end": float(row["end"]), "speaker": row["speaker"].strip()} for row in rows]


def speaker_at(start: float, end: float, mapping: list[dict], fallback: str | None = None) -> str:
    midpoint = (start + end) / 2
    matches = [row for row in mapping if row["start"] <= midpoint <= row["end"]]
    return matches[0]["speaker"] if matches else (fallback or "UNASSIGNED")


def normalize(raw: dict, speaker_map: list[dict], source: Path) -> tuple[list[dict], list[dict]]:
    segments_out: list[dict] = []
    words_out: list[dict] = []
    for index, segment in enumerate(raw.get("segments") or []):
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        if end < start:
            raise ValueError(f"segment {index} ends before it starts")
        speaker = speaker_at(start, end, speaker_map, segment.get("speaker"))
        text = str(segment.get("text", "")).strip()
        normalized = {"index": index, "start": start, "end": end, "speaker": speaker, "text": text, "source": str(source)}
        segments_out.append(normalized)
        for word_index, word in enumerate(segment.get("words") or []):
            word_start = float(word.get("start", start))
            word_end = float(word.get("end", word_start))
            if word_end < word_start:
                raise ValueError(f"word {word_index} in segment {index} ends before it starts")
            words_out.append({
                "segment": index, "word": str(word.get("word", "")).strip(),
                "start": word_start, "end": word_end,
                "speaker": speaker_at(word_start, word_end, speaker_map, speaker),
                "probability": word.get("probability"), "source": str(source),
            })
    if not segments_out:
        raise ValueError("transcript JSON contains no segments")
    return segments_out, words_out


def timestamp(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, value = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{value:06.3f}"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    if not source.is_file():
        print(f"error: source does not exist: {source}", file=sys.stderr)
        return 2
    output = args.output_dir.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        print(f"error: output directory is not empty: {output}", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    try:
        raw, engine_info = run_engine(source, args.engine, args.model, args.language)
        segments, words = normalize(raw, read_speaker_map(args.speaker_map), source)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    cues = []
    phrases = tuple(dict.fromkeys([*DEFAULT_CUES, *(cue.casefold() for cue in args.cue)]))
    for segment in segments:
        folded = segment["text"].casefold()
        for phrase in phrases:
            if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", folded):
                cues.append({
                    "start": segment["start"], "end": segment["end"], "speaker": segment["speaker"],
                    "cue": phrase, "context": segment["text"], "source": str(source),
                })

    markdown = ["# Readable transcript", "", f"Source: `{source}`", ""]
    for segment in segments:
        markdown.append(f"**{timestamp(segment['start'])}–{timestamp(segment['end'])} · {segment['speaker']}**")
        markdown.extend(["", segment["text"] or "[no speech text]", ""])
    (output / "transcript.md").write_text("\n".join(markdown).rstrip() + "\n", encoding="utf-8")
    write_csv(output / "segments.csv", segments, ["index", "start", "end", "speaker", "text", "source"])
    write_csv(output / "words.csv", words, ["segment", "word", "start", "end", "speaker", "probability", "source"])
    write_csv(output / "production_cues.csv", cues, ["start", "end", "speaker", "cue", "context", "source"])
    summary = {
        "source": str(source), **engine_info, "language": raw.get("language"),
        "segments": len(segments), "words": len(words), "production_cues": len(cues),
        "speakers": sorted({segment["speaker"] for segment in segments}),
        "word_timestamps_present": bool(words),
        "speaker_labels_present": any(segment["speaker"] != "UNASSIGNED" for segment in segments),
        "speaker_map_applied": args.speaker_map is not None,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(output)
    if not words:
        print("warning: no word timestamps were present; rerun transcription with word timestamps enabled", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
