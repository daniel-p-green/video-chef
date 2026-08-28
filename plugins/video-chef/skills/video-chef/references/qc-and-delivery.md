# QC and delivery

## Structural checks

On the fresh output, verify container, codec, dimensions, display aspect, duration, frame rate/cadence, pixel format, audio streams, sample rate, channel layout, subtitle streams, and expected file size. Decode the entire file and record any errors. A successful `ffprobe` alone does not prove decodability.

## Editorial review

Watch the complete candidate at normal speed and intended aspect. Check the opening, story clarity, rhythm, transitions, continuity, graphic timing, captions, ending, and whether any important source meaning changed. Inspect the actual phone-size or presentation-size experience when that is the destination.

## Picture review

Check framing, safe areas, crop, sharpness, exposure, color continuity, generated or repair artifacts, flashes, black frames, duplicate or frozen frames, and source/candidate identity consistency. Use matched A/B frames for restoration or appearance work.

## Sound review

Listen end to end on an appropriate device. Check intelligibility, sync, edits, breaths, room-tone jumps, noise-reduction artifacts, music rights and balance, stereo/mono behavior, and beginning/end fades. Metering and waveform inspection support but do not replace listening.

## Claim the right status

- `rendered`: file exists.
- `decoded`: full decode completed without reported errors.
- `technically verified`: requested structural, picture, and sound checks passed.
- `review candidate`: suitable for the named reviewer, with remaining creative decisions listed.
- `owner approved`: named owner reviewed the actual candidate and approved it.
- `delivered`: intended external destination or recipient is confirmed.

## Handoff contents

Provide the candidate or master, editable project or interchange when requested, source map, edit plan, transcript/selects, rights/open-asset list, and QA report. State what changed, what was verified, what remains unverified, and the smallest remaining decision. Never call a file final merely because its filename says `final`.
