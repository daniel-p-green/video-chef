# Transcripts and selects

Retain readable paragraphs, word-level timing when available, speaker labels, source timecode, language, and uncertainty. Mark overlaps, restarts, fillers, off-camera direction, producer cues, hard-to-hear words, and corrections.

For every recommended take, record accuracy, delivery, pacing, picture usability, audio usability, continuity, and why it fits the beat. Do not hide tradeoffs behind one numeric score.

Use the schema:

`beat, source, in, out, speaker, transcript/action, rationale, picture note, audio note, rights, alternate, confidence`

Transcription tools accelerate discovery but need human correction for names, technical terms, accents, crosstalk, and quotes intended for publication.

## Executable transcript workflow

`../../scripts/transcript_workbench.py` accepts either local media or Whisper-compatible JSON. For local media, choose `--engine whisper` or `--engine mlx-whisper` and provide `--model` explicitly; the script does not hide model selection or a possible model download. It requests word timestamps and writes:

- `transcript.md` for readable review;
- `segments.csv` and `words.csv` with source timing;
- `production_cues.csv` for phrases such as producer approvals, resets, and retakes;
- `summary.json` recording engine, model, language, timing availability, and speaker state.

Whisper transcription is not speaker diarization. Supply a reviewed `start,end,speaker` map—beginning with `../../assets/SPEAKER_MAP.template.csv`—or use a separate diarization-capable tool and retain its model and confidence. `UNASSIGNED` is an honest state; never invent speaker identity from transcript wording.
