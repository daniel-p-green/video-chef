---
name: adobe-video-automation
description: Design, write, inspect, and safely run Adobe UXP, ExtendScript, or expression-based automation for Premiere Pro, After Effects, Media Encoder, Animate, and Illustrator video workflows. Use when a concrete Adobe project needs scripted timeline, composition, render, motion, or asset operations; do not use for ordinary manual editing advice or native C++ plugin development.
---

# Adobe Video Automation

Automate the installed Adobe application without guessing its object model or treating a successful script launch as proof of a correct edit.

## Route to the relevant guide

- Modern Premiere Pro UXP tools and current DOM APIs: read [premiere-uxp.md](references/premiere-uxp.md). For legacy ExtendScript, CEP, or QE-era automation, also read [premiere-pro.md](references/premiere-pro.md).
- After Effects projects, items, comps, layers, properties, render queue, text, masks, and expressions: read [after-effects.md](references/after-effects.md). For expression code, also read [after-effects-expressions.md](references/after-effects-expressions.md).
- Adobe Media Encoder queueing, status, and output automation: read [media-encoder.md](references/media-encoder.md).
- Animate documents, timeline assets, and publishing support for motion-graphics work: read [animate.md](references/animate.md).
- Illustrator generation or preparation of editable video graphics: read [illustrator.md](references/illustrator.md).
- Shared ExtendScript language, file I/O, ScriptUI, BridgeTalk, debugging, reflection, and compatibility: read [extendscript-runtime.md](references/extendscript-runtime.md).
- For the complete repository list, maintenance status, and evidence rules, read [sources-and-status.md](references/sources-and-status.md).

## Before writing code

1. Identify the exact application, installed version, operating system, project file, active sequence or composition, and requested result.
2. Determine the supported automation surface for that version. Search the matching guide for the exact object, property, method signature, return value, and stated caveats.
3. Inspect existing project structure and nearby scripts. Resolve item names, IDs, time units, frame rates, track/layer indices, and path conventions from the real project rather than assuming them.
4. Choose the smallest reversible operation. Prefer a duplicated project, sequence, composition, or test asset for mutations.
5. Define observable success: project object created or changed, expected render queued, output decoded, or exact property value verified.

## Implementation rules

- Prefer Adobe's official Premiere UXP documentation for supported current Premiere versions. Treat docsforadobe guides as community-maintained references derived from Adobe documentation; they are useful but not a live guarantee of support in the installed app.
- Do not invent APIs. When a method is missing from the relevant guide or differs at runtime, inspect the live object model or current official Adobe developer documentation and report the mismatch.
- Keep supported public APIs distinct from QE, command IDs, undocumented properties, and third-party type declarations. Use an undocumented surface only when the user accepts the compatibility risk and no supported path meets the need.
- Avoid name-only selection when duplicate items or sequences may exist. Prefer stable identifiers when exposed; otherwise constrain the search and fail on ambiguity.
- Convert seconds, frames, ticks, and display time explicitly. Preserve source and sequence cadence.
- Validate file paths before launching Adobe. Never overwrite an original project or source-media file by default.
- Make reruns safe where practical: detect an existing generated bin, layer, marker, sequence, comp, or output before creating another.
- Capture script errors with operation and object context. Do not swallow exceptions to make an automation appear successful.
- Do not make publishing, delivery, purchase, upload, or destructive project changes without explicit authority.

## Verification

After execution, re-open or query the affected project objects, render a small representative range when visuals changed, and inspect the actual output. For a final render, probe and decode the fresh file and perform normal-speed picture and sound review. Report the strongest proven state: script executed, project mutated as intended, render created, technically verified, or owner approved.
