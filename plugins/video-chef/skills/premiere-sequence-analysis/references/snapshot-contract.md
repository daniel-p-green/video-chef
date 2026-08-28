# Active sequence snapshot contract

Schema version `1.0` records:

- capture timestamp and connector version;
- project name, local path, and GUID;
- active sequence name, GUID, duration, frame size, and timebase;
- video and audio track order, name, ID, and mute state;
- each clip instance's display name, timeline in/out, source in/out, disabled state, project item name, and media path.

Times are decimal seconds. Track indices are zero-based, matching the Premiere API. Items are ordered by timeline start within each track.

The snapshot intentionally excludes frames, waveforms, transcript text, effects, keyframes, captions, markers, render state, and approval state. Those require separate evidence.

Project and media paths can expose names, clients, or private directory structure. Keep the original snapshot local and redact paths before sharing it.
