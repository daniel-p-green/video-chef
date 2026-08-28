# Changelog

## 1.2.3 — 2026-08-27

- Added bounded automatic reconnect after a running Premiere broker is restarted or starts after the panel, while preserving explicit disconnect and token-forget behavior.
- Added a UXP regression test that simulates broker loss, retry, re-registration, and successful recovery without manual token entry.

## 1.2.2 — 2026-08-27

- Replaced the macOS-incompatible plain-HTTP Premiere loopback transport with TLS 1.2+ on `https://127.0.0.1:17841`.
- Added per-machine `mkcert` leaf-certificate setup without silently installing or exporting the local CA.
- Expanded doctor checks for the exact loopback HTTPS manifest allowlist, certificate/key presence, private-key permissions, key-pair validity, and macOS trust evaluation.
- Added certificate-verified HTTPS broker and UXP endpoint regression coverage while preserving token authentication and the read-only capability guard.
- Correctly casts base Premiere project items to `ClipProjectItem` before resolving source-media paths, restoring provenance evidence in live snapshots.

## 1.2.1 — 2026-08-27

- Hardened the Premiere connector with heartbeat-based liveness, clean instance unregister, authenticated status reporting, request timeouts, and private-network preflight support.
- Added Adobe UXP secure-storage token caching with explicit disconnect and forget controls.
- Expanded live ping evidence with Premiere, connector, active-project, and active-sequence identity.
- Added partial-snapshot issue reporting and caption-track counts while retaining schema 1.0 analysis compatibility.
- Made Adobe developer mode an explicit doctor prerequisite instead of allowing package checks to imply live readiness.

## 1.2.0 — 2026-08-27

- Added an original localhost-only, token-authenticated Premiere broker and bundled UXP panel with explicit capability negotiation.
- Added live read-only active-project and active-sequence snapshots with exact track, clip, source, and timeline evidence.
- Added active-sequence structural and narrative reporting with explicit metadata-versus-human-review boundaries.
- Added digest-identified, plan-only transcript/selects rough-cut assembly with mandatory isolated target-sequence naming.
- Added setup/doctor, protocol, privacy, and future write-connector safety contracts.
- Added behavioral and security tests for broker authentication, mutation rejection, round-trip requests, snapshots, and rough-cut plans.

## 1.1.0 — 2026-08-27

- Added whole-project asset inventory covering media, graphics, brand files, documents, captions, fonts, and editable projects.
- Added executable local Whisper/MLX Whisper transcript processing with word timing, reviewed speaker maps, and production-cue detection.
- Added scene-boundary detection and bounded frame-sequence extraction for detailed picture and animation inspection.
- Added full-runtime screen-review and speaker-map records.
- Added an explicit source-fidelity map and corrected attribution to Brent Schooley.
- Expanded functional tests for the new workflows.

## 1.0.0 — 2026-08-27

- Added eight routed professional video-production skills.
- Added current Premiere UXP and complete docsforadobe scripting-guide routing.
- Added hashed media inventory, contact sheets, full-file QC, subtitle QC, and project initialization.
- Added professional brief, edit, selects, rights, audio, caption, decision, delivery, and QA records.
- Added public marketplace packaging, tests, and continuous validation.
