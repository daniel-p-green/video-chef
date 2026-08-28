---
name: video-media-intelligence
description: Inventory and inspect video, audio, screen recordings, graphics, transcripts, takes, scenes, continuity, technical quality, and story coverage to produce a source map and evidence-backed selects. Use before editorial or when diagnosing source problems; do not use to approve the creative cut or deliver a final master.
---

# Video Media Intelligence

Convert opaque media folders into a traceable source map. Technical metadata, transcripts, and sampled frames are evidence inputs, not substitutes for watching and listening.

## Workflow

1. Resolve the search scope, canonical sources, proxies, alternates, sync relationships, project files, and prior exports.
2. Run `../../scripts/media_inventory.py` and, when visual overview helps, `../../scripts/make_contact_sheet.py`.
3. Transcribe dialogue in readable and word-timed forms when supported; preserve speaker labels, source file, source range, tool/model, language, and uncertainty.
4. Group duplicate or alternate takes. Compare accuracy, delivery, pacing, picture, sound, continuity, and production cues separately.
5. Inspect exact selected ranges for focus, exposure, motion, crop, private information, screen state, background, lighting, appearance, and audio defects.
6. Compare the locked brief or script with available coverage. Classify gaps as reshoot/rerecord, alternate-source, transparently coverable, rights-dependent, or optional.
7. Write source-linked selects using `../../assets/SELECTS.template.csv` and record rights/provenance in `../../assets/RIGHTS_LOG.template.csv`.

## Evidence rules

- Every quote or select must resolve to a real source path and time range.
- Check automated transcript wording against source audio before treating it as a quote.
- Do not infer emotion, identity, consent, or factual truth from appearance alone.
- Detecting a face, waveform, scene, or keyword does not establish editorial importance.
- Keep a rejected alternate when it may solve a technical or continuity issue later.
- If a file set is suspiciously narrow, check one or two plausible alternate locations before reporting it missing.

Read [transcripts-and-selects.md](references/transcripts-and-selects.md) for dialogue and take comparison, and [visual-continuity-and-gaps.md](references/visual-continuity-and-gaps.md) for picture inspection and coverage analysis.
