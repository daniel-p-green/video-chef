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

1. If no private config exists, run `python3 ../../scripts/premiere_bridge.py init`. Do not use `--force` unless the user explicitly wants to rotate the token.
2. Run `python3 ../../scripts/premiere_bridge.py setup-tls`. This uses `mkcert` to generate a leaf certificate and private key beside the private config. It does not install or export the local CA. Never commit either file.
3. Run `python3 ../../scripts/premiere_bridge.py doctor`. This checks Premiere Pro 25.6+, UXP Developer Tool 2.2+, Adobe developer mode, the packaged connector, the private config, the TLS key pair, restrictive permissions, and macOS trust. If macOS trust fails, explain the security implications of a local CA before asking the user to run `mkcert -install`; do not run that trust-changing command silently.
4. Load `../../premiere-uxp/video-chef-bridge/manifest.json` in Adobe UXP Developer Tool, launch it in the installed supported Premiere version, and open **Video Chef Bridge** from Premiere's Plugins menu.
5. Start the broker with `python3 ../../scripts/premiere_bridge.py serve`.
6. Copy the token directly from the private config into the UXP panel and connect. Do not echo it through terminal output.
7. Prove the round trip with `python3 ../../scripts/premiere_bridge.py request ping`.

Run `python3 ../../scripts/premiere_bridge.py status` when diagnosing a connection. Exit `0` means the authenticated connector heartbeat is live; exit `2` means the broker answered but no live connector is polling. After the first successful connection, the panel can cache the token in UXP secure storage. **Forget token** removes that cache.

Adobe's current UXP network guide says Premiere on macOS disallows plain HTTP. Connector 1.2 therefore uses certificate-verified loopback HTTPS and an exact manifest allowlist; do not weaken it to broad network access or disable certificate verification. A passing doctor still does not prove Premiere accepted the transport, so the live ping is required. A registered connector with a stale heartbeat is treated as disconnected rather than timing every request out.

Loading or launching a UXP plugin changes local Adobe development state. Do it only when the user asked to set up or use the bridge; doctor alone is read-only.

## Capture exact sequence evidence

Run:

```bash
python3 ../../scripts/premiere_bridge.py request snapshot_active_sequence --output bridge-response.json
```

The returned file is a broker envelope. `premiere_sequence_analysis.py` accepts it directly and can also preserve a validated extracted snapshot. Preserve the capture time, project path and GUID, sequence GUID, track order, source paths, and source/timeline ranges. Redact local paths before sharing either file publicly.

Read [bridge-protocol.md](references/bridge-protocol.md) when diagnosing transport, permissions, version mismatch, timeout, or capability errors.
