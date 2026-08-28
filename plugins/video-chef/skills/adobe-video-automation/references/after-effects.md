# After Effects scripting

Source: https://github.com/docsforadobe/after-effects-scripting-guide

Use the guide for the application and project model; footage, folders, comps, layers, properties, text, masks, render queue, settings, and related collections.

## Decision rules

- Resolve the exact project, composition, layer, and property path. Duplicate a comp or project for uncertain changes.
- Wrap a coherent user-facing mutation in one undo group when supported, and close it reliably even on error.
- Treat layer index, item index, display name, match name, property hierarchy, and selected state as different identifiers. Prefer match names where localization affects display names.
- Use composition frame rate and duration explicitly. Check whether a time value is seconds, frames, or a time object.
- Preserve expressions, keyframes, interpolation, parenting, track mattes, blending, collapse transformations, 3D state, and effect order unless the request changes them.
- For text and motion graphics, verify fonts, missing footage, expression errors, safe areas, and rendered readability.
- For render-queue automation, confirm output module, render settings, destination, status, and completed file before reporting success.

## Useful guide areas

Search `docs/general`, `docs/item`, `docs/layer`, `docs/property`, `docs/text`, `docs/renderqueue`, and `docs/other`. Read the object-model overview and changelog when compatibility matters.
