---
name: video-audio-captions
description: Prepare, clean, mix, measure, caption, subtitle, transcribe, or plan audio description for a video while preserving dialogue and accessibility. Use for dialogue editing, noise repair, music/SFX balance, loudness, SRT/WebVTT, caption QA, and accessible media; do not use for picture editorial or color finishing.
---

# Video Audio and Captions

Make speech intelligible and access complete without flattening the voice or treating a meter as a listening decision.

## Route

- Dialogue edit, sync, cleanup, ambience, music, SFX, mix, or loudness: read [audio-post.md](references/audio-post.md).
- Captions, subtitles, transcripts, speaker labels, non-speech audio, or audio description: read [captions-accessibility.md](references/captions-accessibility.md).

## Workflow

1. Resolve the locked picture or explicitly label the audio/caption work as provisional.
2. Preserve original production audio and sync. Work on derived files or reversible NLE effects.
3. Diagnose each audible problem in context before choosing repair; prefer local repair over broad processing.
4. Build dialogue first, then room tone/ambience, music, and SFX according to the brief and rights log.
5. Measure loudness and peaks against the written destination specification. No single loudness target fits every delivery.
6. Listen end to end, including opening, edits, breaths, transitions, and ending, on an appropriate playback path.
7. Create captions from the checked dialogue, then human-correct wording, names, timing, line breaks, speaker labels, and meaningful sound cues.
8. Run `../../scripts/subtitle_qc.py`, inspect captions over the actual picture, and complete `../../assets/CAPTION_QA.template.md`.

## Hard boundaries

- Do not remove breaths, room tone, accent, emotion, or texture merely because a tool can.
- Do not claim repair success from spectral plots, waveforms, transcript text, or loudness numbers alone.
- Music and SFX require known rights and explicit creative approval.
- Automated captions are drafts. W3C notes that captions include spoken words, necessary speaker identity, and important sounds, synchronized with the picture.
- When important visual information is not conveyed by dialogue, assess descriptive transcript or audio-description needs rather than assuming captions solve it.

Use `../../assets/AUDIO_POST.template.md` to record processing and listening gates.
