# Analysis and selects

## Build a source map

Inventory cameras, screen recordings, production audio, music/SFX, graphics, scripts, transcripts, brand rules, NLE projects, proxies, and prior exports. Record file role, duration, dimensions, cadence, codec, audio layout, modification time, and suspected relationships. Treat same-named or visually similar files as unverified until checked.

Use `../../scripts/media_inventory.py` when `ffprobe` is available. The inventory is technical evidence only.

## Dialogue and timing

When dialogue drives the story, produce a readable transcript, word-level timestamps when supported, speaker labels, source filename and timecode for every quote, and uncertainty flags for names, technical terms, overlap, and hard-to-hear words.

Mark restarts, filler, pauses, off-camera direction, producer approval cues, duplicate takes, and clean verbal transitions. Do not treat an automated transcript as an authoritative quote without checking the source audio around the selected range.

## Selects

Compare takes by accuracy, delivery, pacing, picture usability, audio usability, continuity, and team cues. Do not collapse those dimensions into an unexplained score. For each recommended select, record:

`beat | source | in | out | transcript | why this take | known issue | alternate`

Keep rejected alternatives visible when they may solve a continuity, performance, or technical problem later.

## Picture inspection

Use scene detection or evenly sampled frames to locate candidate moments, then inspect the exact ranges used in the edit. Check composition, expression, angle, background, focus, exposure, motion, artifacts, screen readability, cursor/click behavior, sensitive information, wardrobe/appearance, lighting, and movement across cuts.

For demo footage, verify that the screen state supports the spoken claim and that private or unreleased information is absent or explicitly masked.

## Gap pass

Before editing, compare the locked story and script to available sources. Flag missing dialogue, demo steps, discussion topics, transitions, cutaways, graphics, room tone, and rights/brand assets. Separate must-reshoot gaps, gaps solvable with alternates, gaps transparently coverable with existing or approved material, and optional enhancements. Do not manufacture a seamless result that hides a material source gap from the user.
