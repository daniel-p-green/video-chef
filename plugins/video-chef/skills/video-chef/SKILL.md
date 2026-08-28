---
name: video-chef
description: Coordinate an end-to-end professional video project across story, footage analysis, editorial, audio, captions, motion graphics, finishing, Adobe automation, review, and delivery. Use when a request spans multiple production stages or the correct specialist route is unclear; use a narrower Video Chef skill for one-stage work.
---

# Video Chef

Coordinate the production; route each stage to the matching sibling skill. Build the story before the timeline, preserve editable lineage, and never confuse a successful render with an approved film.

## Specialist routing

- Brief, audience, story architecture, runtime, format, tone, or preproduction lock: use `video-story`.
- Media inventory, transcript, diarization, scene or shot inspection, selects, continuity, or missing coverage: use `video-media-intelligence`.
- Paper edit, assembly, multicam, pacing, NLE timeline construction, versioning, or recut: use `video-editorial`.
- Dialogue cleanup, mix planning, loudness, captions, subtitles, transcripts, or audio description: use `video-audio-captions`.
- Titles, lower thirds, motion language, screen graphics, visual systems, or phone-scale proofing: use `video-motion-graphics`.
- Conform, color, restoration, master/export specifications, automated QC, review, or delivery: use `video-finishing-delivery`.
- Premiere Pro, After Effects, Media Encoder, Animate, or Illustrator scripting: use `adobe-video-automation`.
- Premiere bridge setup, diagnostics, connectivity, or an exact live active-sequence snapshot: use `premiere-bridge`.
- Evidence-backed structural or narrative analysis of the active Premiere sequence: use `premiere-sequence-analysis`.
- Transcript/selects-driven Premiere rough-cut planning with isolated target-sequence safeguards: use `premiere-rough-cut`.

For a narrow mechanical task such as trim, transcode, resize, extract audio, or generate a proxy, inspect the input and perform only that operation; do not impose the full workflow.

## Production state model

Keep these states distinct:

1. `exploratory` — references, tests, and possible directions.
2. `planned` — brief and edit plan exist; assumptions may remain.
3. `review candidate` — a complete playable render exists and passes stated preflight checks.
4. `technically verified` — the fresh file decoded and requested picture, sound, caption, and spec checks passed.
5. `owner approved` — the user or named owner reviewed the actual result.
6. `delivered` — the intended destination or recipient is externally confirmed.

Never infer a later state from an earlier one. A contact sheet, transcript, proxy, timeline, graphics proof, or successful export proves only itself.

## Production invariants

- Resolve the canonical source, project, active sequence or composition, proxies, alternates, previous exports, and owner-approved decisions before mutation.
- Treat originals as immutable. Separate sources, analysis, editable projects, experiments, review candidates, masters, and delivery copies.
- Preserve testimony, natural identity, time relationships, and provenance. Generated material must be labeled and must not masquerade as captured evidence.
- Prefer isolated project copies, sequences, or compositions for experiments. Do not flatten or overwrite the only editable master.
- Ask before purchases, credit spend, uploads of private media, publishing, external delivery, or destructive project changes.
- Render the smallest representative proof first when appearance, restoration, reframing, color, graphics, audio treatment, or expensive generation is uncertain.
- Technical measurement supports human review; it does not replace normal-speed viewing, sound-on listening, or owner judgment.

## End-to-end production spine

1. Create or resolve the workspace, canonical sources, owner, delivery destination, and authority boundaries.
2. Lock audience, story, runtime range, format, and feeling before a narrative edit.
3. Inventory, transcribe, inspect, select, and identify source or rights gaps.
4. Approve a source-linked paper edit, then construct the editable timeline.
5. Prove uncertain treatments on a short representative range.
6. Finish picture, dialogue, mix, captions, and graphics against a written delivery specification.
7. Run deterministic full-file checks, then complete normal-speed picture and sound review.
8. Obtain owner approval of the actual candidate before delivery; confirm delivery separately.

## Shared production kit

- `../../scripts/init_video_project.py`: safe project structure and production records.
- `../../scripts/media_inventory.py`: recursive `ffprobe` inventory with optional hashes.
- `../../scripts/asset_inventory.py`: all-file production inventory with role suggestions and optional hashes.
- `../../scripts/make_contact_sheet.py`: evenly sampled frame sheet.
- `../../scripts/scene_detect.py`: scene-boundary manifest and optional boundary frames.
- `../../scripts/extract_frame_sequence.py`: bounded timestamped frames for close motion inspection.
- `../../scripts/transcript_workbench.py`: local Whisper or Whisper-JSON transcript, word timing, speaker-map, and production-cue records.
- `../../scripts/media_qc.py`: full decode, black/freeze detection, and loudness report.
- `../../scripts/subtitle_qc.py`: SRT/WebVTT timing and readability checks.
- `../../scripts/premiere_bridge.py`: localhost-only, token-authenticated broker, setup, doctor, and allowlisted read requests for the bundled Premiere UXP connector.
- `../../scripts/premiere_sequence_analysis.py`: validates an active-sequence snapshot and produces a timestamped structural evidence report.
- `../../scripts/premiere_rough_cut.py`: builds a deterministic, source-linked, plan-only rough-cut record for a new isolated sequence.
- `../../assets/`: brief, edit plan, selects, rights, audio, captions, decision, delivery, and QA templates.

The source roadmap is summarized in [source-notes.md](references/source-notes.md). The older detailed references remain valid fallbacks when a specialist skill is unavailable.
