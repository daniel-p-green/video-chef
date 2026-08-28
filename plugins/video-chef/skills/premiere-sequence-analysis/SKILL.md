---
name: premiere-sequence-analysis
description: Analyze an active Premiere Pro sequence from a Video Chef bridge snapshot and produce an evidence-backed structural and narrative review. Use when the user asks what is in the active timeline, whether the sequence reflects a story, where pacing or coverage problems may be, or requests a timestamped Premiere sequence analysis; do not infer visual or audio quality from timeline metadata alone.
---

# Premiere Sequence Analysis

Use live timeline evidence as the structural layer of an editorial analysis, then add transcript, frame, and sound evidence only when available.

## Workflow

1. Use `premiere-bridge` to capture the active sequence. Preserve its project and sequence identity.
2. Extract the `result.data` snapshot from the broker envelope.
3. Run `python3 ../../scripts/premiere_sequence_analysis.py snapshot.json PREMIERE_SEQUENCE_REPORT.md`.
4. Use the report to establish sequence duration, dimensions, tracks, clip instances, source ranges, disabled items, and timeline order.
5. For narrative judgments, join the snapshot with a word-timed transcript or selects record. For visual judgments, sample the actual export or source frames. For audio judgments, listen and measure the actual mix.
6. Report evidence and interpretation separately. Cite timeline ranges for every conclusion and label unknowns.

## Narrative review frame

Assess the active sequence against the locked Video Chef brief:

- opening hook and first meaningful information;
- core message and evidence supporting it;
- order and duration of story beats;
- repetition, dead time, unsupported claims, and missing context;
- final takeaway or action;
- whether runtime, platform framing, and tone match the brief.

Timeline metadata can reveal order, duration, gaps, source reuse, disabling, and track complexity. It cannot reveal what a frame depicts, whether a sentence is understandable, whether an edit feels smooth, or whether music and dialogue balance correctly. Never upgrade structural evidence into those claims.

Read [snapshot-contract.md](references/snapshot-contract.md) for field meaning and privacy boundaries.
