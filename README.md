# Video Chef

![Video Chef icon](plugins/video-chef/assets/icon.png)

Video Chef is a professional, source-faithful video-production plugin for Codex. It coordinates story development, media intelligence, editable editorial work, audio and captions, motion graphics, finishing, Adobe automation, technical QC, human review, and verified delivery.

## Install in Codex

```bash
codex plugin marketplace add daniel-p-green/video-chef
codex plugin add video-chef@video-chef
```

Start a new Codex task after installation so the skills are loaded.

## What it includes

| Skill | Purpose |
|---|---|
| `video-chef` | Coordinates an end-to-end production and routes specialist work |
| `video-story` | Locks audience, story, runtime, format, tone, and preproduction decisions |
| `video-media-intelligence` | Inventories media, transcripts, selects, continuity, and coverage gaps |
| `video-editorial` | Builds source-linked paper edits and editable NLE timelines |
| `video-audio-captions` | Handles dialogue, mix, loudness, captions, transcripts, and accessibility |
| `video-motion-graphics` | Designs and proves titles and motion systems inside the real edit |
| `video-finishing-delivery` | Conforms, restores, color-manages, exports, QCs, and verifies delivery |
| `adobe-video-automation` | Routes safe Premiere, After Effects, Media Encoder, Animate, and Illustrator automation |

The Adobe skill includes all scripting guides published by the docsforadobe organization and prioritizes Adobe's official Premiere UXP documentation for current Premiere development.

## Production tools

- `init_video_project.py` creates a non-destructive production workspace and records.
- `media_inventory.py` produces recursive `ffprobe` inventories with optional SHA-256 hashes.
- `make_contact_sheet.py` creates evenly sampled visual sheets.
- `media_qc.py` performs full decode, black/freeze detection, and EBU loudness analysis.
- `subtitle_qc.py` checks SRT/WebVTT timing, overlap, line length, line count, and reading speed.

The plugin also includes templates for the creative brief, edit plan, selects, rights, audio post, caption QA, delivery specification, decision/change lineage, and master QA.

## Production philosophy

- Build the story before the timeline.
- Keep original media and canonical editable projects intact.
- Tie every select and quote to a real source range.
- Prove uncertain creative or identity-affecting treatments on a short representative sample.
- Treat generated material as generated, never as captured evidence.
- Separate rendered, decoded, technically verified, owner-approved, and delivered states.
- Automated checks support—but do not replace—normal-speed picture review, sound-on listening, and human approval.

## Requirements

- Codex with plugin marketplace support.
- Python 3.10 or later for included helper scripts.
- `ffmpeg` and `ffprobe` for media inventory, contact sheets, and automated QC.
- Adobe applications only when using the Adobe automation skill.

Destination-specific codec, loudness, caption, accessibility, and platform requirements can change. Video Chef records and verifies the intended delivery specification rather than assuming one universal preset.

## Development

```bash
python3 -m unittest discover -s tests -v
```

The test suite validates package structure and runs behavioral media, caption, and project-initialization checks when FFmpeg is available.

## License

Video Chef's original code and documentation are available under the MIT License. Linked Adobe and docsforadobe documentation remains under its respective ownership and terms; those guides are referenced, not redistributed.
