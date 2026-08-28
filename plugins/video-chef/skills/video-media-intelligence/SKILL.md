---
name: video-media-intelligence
description: Inventory and inspect video, audio, screen recordings, graphics, transcripts, takes, scenes, continuity, technical quality, and story coverage to produce a source map and evidence-backed selects. Use before editorial or when diagnosing source problems; do not use to approve the creative cut or deliver a final master.
---

# Video Media Intelligence

Convert opaque media folders into a traceable source map. Technical metadata, transcripts, and sampled frames are evidence inputs, not substitutes for watching and listening.

## Workflow

1. Resolve the search scope, canonical sources, proxies, alternates, sync relationships, project files, and prior exports.
2. Run `../../scripts/asset_inventory.py` for the full production package and `../../scripts/media_inventory.py` for technical media metadata. Confirm camera, screen, audio, graphics, scripts, brand guides, templates, project files, and prior exports rather than trusting role guesses.
3. Transcribe dialogue in readable and word-timed forms with `../../scripts/transcript_workbench.py` or a documented equivalent. Preserve speaker labels, source file, source range, tool/model, language, and uncertainty; use `../../assets/SPEAKER_MAP.template.csv` when diarization comes from another tool.
4. Group duplicate or alternate takes. Compare accuracy, delivery, pacing, picture, sound, continuity, and production cues separately.
5. Start picture discovery with `../../scripts/scene_detect.py` or an evenly sampled contact sheet, then inspect exact selected ranges. Use `../../scripts/extract_frame_sequence.py` for a bounded frame-by-frame look at motion, transitions, or animation timing.
6. For every screen recording, review the complete runtime in chronological order and record key actions, readability, script match, missing steps, and private or unreleased information in `../../assets/SCREEN_REVIEW.template.csv`. Sampling may guide attention but does not replace the full pass.
7. Compare the locked brief or script with available coverage. Classify gaps as reshoot/rerecord, alternate-source, transparently coverable, rights-dependent, or optional.
8. Write source-linked selects using `../../assets/SELECTS.template.csv` and record rights/provenance in `../../assets/RIGHTS_LOG.template.csv`.

## Evidence rules

- Every quote or select must resolve to a real source path and time range.
- Check automated transcript wording against source audio before treating it as a quote.
- Do not infer emotion, identity, consent, or factual truth from appearance alone.
- Detecting a face, waveform, scene, or keyword does not establish editorial importance.
- Keep a rejected alternate when it may solve a technical or continuity issue later.
- If a file set is suspiciously narrow, check one or two plausible alternate locations before reporting it missing.
- Local transcription engines may download model files. Make the model choice and any download explicit before running; do not upload private media without authorization.

Read [transcripts-and-selects.md](references/transcripts-and-selects.md) for dialogue and take comparison, and [visual-continuity-and-gaps.md](references/visual-continuity-and-gaps.md) for picture inspection and coverage analysis.
