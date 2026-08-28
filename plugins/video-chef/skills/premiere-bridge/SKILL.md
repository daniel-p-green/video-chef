---
name: premiere-bridge
description: Set up, diagnose, and use Video Chef's localhost-only Premiere Pro UXP bridge to inspect the active project and sequence. Use when Codex needs exact live Premiere timeline evidence, when the bridge is disconnected, or when a user asks to set up or run doctor on Premiere integration; do not use for generic Premiere advice or imply that the bundled read-only connector can modify a timeline.
---

# Premiere Bridge

Connect Codex to the active Premiere session through a private local broker and the bundled UXP panel. Treat connection, inspection, project mutation, rendered output, and human approval as different states.

## Safety boundary

- The bundled connector is read-only. Its allowlist is `ping` and `snapshot_active_sequence`.
- It binds only to `127.0.0.1`, uses a private bearer token, and rejects arbitrary JavaScript and unlisted operations.
- Never paste the token into chat, logs, public issues, or committed files.
- A successful snapshot proves the project and timeline structure returned by Premiere. It does not prove the story works, frames look correct, sound is correct, or a render passes QC.

## Setup and doctor

1. Run `python3 ../../scripts/premiere_bridge.py doctor`. This proves Premiere Pro 25.6+, UXP Developer Tool 2.2+, and the packaged connector shape. A missing private config is a warning, not a failed package.
2. If no private config exists, run `python3 ../../scripts/premiere_bridge.py init`. Do not use `--force` unless the user explicitly wants to rotate the token.
3. Load `../../premiere-uxp/video-chef-bridge/manifest.json` in Adobe UXP Developer Tool, launch it in the installed supported Premiere version, and open **Video Chef Bridge** from Premiere's Plugins menu.
4. Start the broker with `python3 ../../scripts/premiere_bridge.py serve`.
5. Copy the token directly from the private config into the UXP panel and connect. Do not echo it through terminal output.
6. Prove the round trip with `python3 ../../scripts/premiere_bridge.py request ping`.

Adobe's current UXP network guide warns that macOS can restrict plain HTTP. The connector uses loopback HTTP for development and never leaves the machine, but a passing package doctor does not prove Premiere accepted that transport. The ping is the required live transport proof; if it fails with a network permission error, stop and do not weaken the manifest to broad network access.

Loading or launching a UXP plugin changes local Adobe development state. Do it only when the user asked to set up or use the bridge; doctor alone is read-only.

## Capture exact sequence evidence

Run:

```bash
python3 ../../scripts/premiere_bridge.py request snapshot_active_sequence > bridge-response.json
```

The returned file is a broker envelope. Extract `result.data` as the snapshot consumed by `premiere_sequence_analysis.py`. Preserve the capture time, project path and GUID, sequence GUID, track order, source paths, and source/timeline ranges. Redact local paths before sharing the snapshot publicly.

Read [bridge-protocol.md](references/bridge-protocol.md) when diagnosing transport, permissions, version mismatch, timeout, or capability errors.
