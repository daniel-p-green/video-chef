---
name: premiere-rough-cut
description: Turn source-linked transcript selects into a validated, reviewable Premiere rough-cut plan with explicit story order, timing, and an isolated target-sequence policy. Use when the user asks for a transcript-driven rough cut, paper edit translated into timeline instructions, or a guarded Premiere assembly; do not claim the bundled read-only bridge has executed the plan.
---

# Premiere Rough Cut

Build a rough cut only after the audience, story, runtime range, format, and feeling are locked. Separate story selection from timeline execution.

## Required inputs

- A source-linked selects CSV with `source_path`, `source_in`, `source_out`, and `story_order`.
- Prefer `speaker`, `transcript`, and `reason` fields so a reviewer can audit every segment.
- A target frame rate and a new target sequence name beginning with `VC_ROUGH_CUT_`.
- Confirmation of the canonical Premiere project and source media identity before any future execution.

## Build the guarded plan

Run:

```bash
python3 ../../scripts/premiere_rough_cut.py SELECTS.csv ROUGH_CUT_PLAN.json \
  --target-sequence VC_ROUGH_CUT_YYYYMMDD_v01 --fps 29.97
```

The tool validates positive, unique story order; positive source ranges; deterministic timeline placement; target isolation; and a SHA-256 plan identity. It writes `mode: plan_only`, `execution.requested: false`, and records that connector 1.0 cannot apply the plan.

Review the plan against the brief and transcript. Check opening, beat order, runtime, necessary context, repetition, final takeaway, and source fidelity. Resolve ambiguous source paths or overlapping transcript selections before treating it as executable.

## Execution boundary

The bundled Premiere connector is intentionally read-only. Do not describe a JSON plan, project scaffold, imported XML, or script launch as an applied rough cut. A write-capable connector is acceptable only after it proves all of these controls:

1. exact project and source fingerprint match;
2. explicit reviewed plan digest;
3. new isolated target sequence, never the active master;
4. allowlisted typed edit operations, never arbitrary code;
5. Premiere undo transaction and failure-safe restoration;
6. post-edit sequence snapshot compared with the plan;
7. playable export, technical checks, sound-on review, and owner approval as separate later gates.

Read [rough-cut-contract.md](references/rough-cut-contract.md) before designing or evaluating an execution implementation.
