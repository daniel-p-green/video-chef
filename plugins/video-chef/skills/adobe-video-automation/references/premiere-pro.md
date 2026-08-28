# Premiere Pro scripting

Source: https://github.com/docsforadobe/premiere-scripting-guide

Use the guide for `Application`, `Project`, `ProjectItem`, `Sequence`, `Track`, `TrackItem`, markers, components, collections, time, encoder integration, and supported utility methods.

## Decision rules

- Resolve the canonical project and active sequence before mutation. Create a new sequence or isolated project copy for an experiment.
- Confirm whether the requested operation is exposed by the supported scripting DOM. Keep QE DOM calls explicitly labeled as undocumented and version-fragile.
- Inspect bin hierarchy, project item identity, media path, sequence settings, track indices, in/out values, and timebase before placing or moving clips.
- Do not assume that display frame rate, source frame rate, sequence timebase, seconds, frames, or ticks are interchangeable.
- When importing media, verify the resulting project items and relink state. When inserting clips, re-query the track items and their ranges.
- When applying or changing effects, verify component names and properties in the installed version and locale; fail on ambiguity.
- When exporting, preserve an editable project state, confirm preset and output path, wait for completion, then validate the fresh file independently.

## Useful guide areas

Search the repository's `docs/application`, `docs/project`, `docs/sequence`, `docs/item`, `docs/track`, `docs/collection`, and `docs/other` sections for the exact object and method. Use the page's stated return values and version notes; do not infer success from the absence of an exception.
