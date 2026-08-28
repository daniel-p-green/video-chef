# QC and delivery

## Automated checks

Run full decode, stream/format inspection, expected-duration and stream checks, and relevant black/freeze/loudness analysis. FFmpeg documents `blackdetect`, `freezedetect`, and `ebur128` as detectors or analyzers; their findings require editorial interpretation. Source: https://ffmpeg.org/ffmpeg-filters.html

## Human review

Watch the entire fresh file at normal speed and intended aspect. Listen from start through tail. Inspect captions over picture. Check framing, color, artifacts, flashes, black/frozen frames, sync, edits, noise, music balance, text, credits, and ending behavior.

## Package

Keep the editable project, source map, decision/change logs, rights log, caption files, review candidate, mezzanine master, destination encode, delivery spec, and QA report distinct. Use hashes when chain of custody or exact file identity matters.

## Status

`rendered` means the file exists. `decoded` means full decode completed. `technically verified` means the requested spec and media checks passed. `owner approved` requires review of the actual candidate. `delivered` requires confirmation at the intended external destination.
