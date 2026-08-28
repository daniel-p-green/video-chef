# Premiere bridge protocol

## Architecture

The Python broker binds only to `127.0.0.1:17841` with TLS 1.2+. The Premiere UXP panel reaches it through the manifest-compatible `https://localhost:17841` origin. Codex sends certificate-verified requests directly to the loopback address; the connector executes an allowlisted Premiere DOM read and posts the result. All endpoints require the same private bearer token.

The broker uses protocol `1.0`; connector `1.2.2` adds bounded automatic re-registration after broker restarts and when a saved-token panel starts before the broker. It retains connector 1.2.1's macOS-compatible loopback HTTPS and correct clip media-path resolution through Premiere's `ClipProjectItem` API without changing the wire protocol. The connector advertises `ping` and `snapshot_active_sequence`, plus `mutation_enabled: false`. The broker rejects undeclared capabilities, arbitrary operations, and any write request.

## Endpoints

- `POST /v1/connector/register`: connector instance ID, connector version, Premiere version, and capability negotiation.
- `GET /v1/connector/next`: next queued allowlisted job, or HTTP 204.
- `POST /v1/connector/result`: result for an exact job ID.
- `POST /v1/connector/unregister`: remove the matching connector instance cleanly.
- `POST /v1/request`: authenticated Codex request; waits for a matching connector result.
- `GET /v1/status`: protocol, connector heartbeat age/liveness, and mutation state.

## Failure interpretation

- `401`: token mismatch. Reconnect with the token from the private config; do not expose it.
- `409`: protocol versions differ. Use matching broker and UXP connector files from one Video Chef release.
- `503`: no UXP connector is registered, or its heartbeat is stale. Start the broker, launch the panel in Premiere, and connect.
- `504`: Premiere did not answer before the broker timeout. Confirm the panel remains open and Premiere is responsive; retry the read once.
- `501`: the connector does not advertise that capability. Do not bypass negotiation.
- TLS or certificate error: run doctor. Regenerate only the leaf with `setup-tls --force` when needed; do not disable verification or silently trust a new local CA.

## Mutation policy

No write capability exists in connector 1.2.2. A future write connector must use a separate capability version, an isolated new target sequence, a reviewed plan digest, explicit user authorization, an undoable Premiere transaction, post-mutation reinspection, and failure-safe source in/out restoration. A prompt or token alone is not sufficient proof that an edit is safe.
