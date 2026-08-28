# Guarded rough-cut contract

## Plan identity

The plan is an ordered list of absolute source paths and decimal-second source ranges. It also contains derived timeline ranges, frame rate, isolated target sequence name, total duration, and a SHA-256 identity. The digest identifies the reviewed plan; it does not authorize execution by itself.

## Preflight for a future write connector

- Match the live project GUID and path to the reviewed target.
- Resolve every source path to exactly one Premiere project item; fail on missing or ambiguous matches.
- Confirm every source range is within media duration and aligned to the intended cadence.
- Refuse an existing target sequence name unless it is an exact resumable run with matching lineage.
- Require a separate, short-lived execution authorization bound to project GUID, target name, and plan digest.

## Apply and verify

Apply typed operations in an undoable transaction to the new sequence. Never change or delete the active master sequence. If temporary project-item in/out changes are unavoidable, record and restore every original value even on failure.

After apply, capture the new sequence with the bridge and compare every source and timeline range with the plan. A matching snapshot proves structural application only. Export and inspect the actual candidate before editorial, picture, sound, or approval claims.
