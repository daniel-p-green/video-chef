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
| `premiere-bridge` | Sets up and diagnoses a localhost-only, token-authenticated UXP connection to the active Premiere session |
| `premiere-sequence-analysis` | Turns an exact active-sequence snapshot into an evidence-backed structural and narrative review |
| `premiere-rough-cut` | Builds a source-linked, digest-identified rough-cut plan for a new isolated Premiere sequence |

The Adobe skill includes all scripting guides published by the docsforadobe organization and prioritizes Adobe's official Premiere UXP documentation for current Premiere development.

## Production tools

- `init_video_project.py` creates a non-destructive production workspace and records.
- `media_inventory.py` produces recursive `ffprobe` inventories with optional SHA-256 hashes.
- `asset_inventory.py` catalogs media, graphics, brand files, scripts, templates, projects, captions, and other production assets.
- `make_contact_sheet.py` creates evenly sampled visual sheets.
- `scene_detect.py` produces scene-boundary manifests and optional boundary frames.
- `extract_frame_sequence.py` creates bounded timestamped frame runs for animation and motion analysis.
- `transcript_workbench.py` runs local Whisper/MLX Whisper or normalizes existing Whisper JSON into readable, word-level, speaker-aware, and production-cue records.
- `media_qc.py` performs full decode, black/freeze detection, and EBU loudness analysis.
- `subtitle_qc.py` checks SRT/WebVTT timing, overlap, line length, line count, and reading speed.
- `premiere_bridge.py` initializes, provisions per-machine loopback TLS, diagnoses, serves, reports live connector heartbeat status, queries the private read-only Premiere bridge, and can atomically preserve exact response envelopes for downstream analysis.
- `premiere_sequence_analysis.py` validates live sequence snapshots and writes timestamped evidence reports.
- `premiere_rough_cut.py` validates transcript selects and creates a deterministic plan-only assembly record.

The plugin bundles an original Premiere UXP panel under `premiere-uxp/video-chef-bridge`. Connector 1.2 is intentionally read-only: it can prove live connectivity over loopback HTTPS, securely cache the private token in Adobe UXP storage, and inspect the active project and sequence, but it cannot alter a timeline. Rough-cut execution remains gated until a write-capable connector can prove project identity, plan identity, isolated sequence creation, undoability, post-edit reinspection, and failure-safe restoration inside Premiere.

The plugin also includes templates for the creative brief, edit plan, selects, rights, speaker mapping, full-runtime screen review, audio post, caption QA, delivery specification, decision/change lineage, and master QA.

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
- Local OpenAI Whisper or MLX Whisper is optional for direct transcription; existing Whisper JSON can be processed without either engine. Model selection and downloads are explicit.
- Adobe applications only when using the Adobe automation skill.
- Premiere Pro 25.6 or later, Adobe UXP Developer Tool 2.2 or later, and `mkcert` when using the live Premiere bridge. Adobe's manifest grammar allowlists the loopback HTTPS domain as `https://localhost`; the connector itself uses only port `17841`, and the broker binds only that port on `127.0.0.1`. Video Chef generates a per-machine leaf certificate but never installs a local root CA silently; users must review that trust decision themselves. A successful in-Premiere ping remains the required live transport proof.

Destination-specific codec, loudness, caption, accessibility, and platform requirements can change. Video Chef records and verifies the intended delivery specification rather than assuming one universal preset.

## Development

```bash
python3 -m unittest discover -s tests -v
```

The test suite validates package and UXP structure, broker authentication and capability guards, synthetic connector round trips, active-sequence evidence, guarded rough-cut plans, asset discovery, the Whisper CLI contract, transcript timing and cues, scene detection, bounded frame extraction, media QC, captions, and project initialization.

## License

Video Chef's original code and documentation are available under the MIT License. Linked Adobe and docsforadobe documentation remains under its respective ownership and terms; those guides are referenced, not redistributed.
