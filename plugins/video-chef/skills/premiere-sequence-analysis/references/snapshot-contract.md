# Active sequence snapshot contract

Schema versions `1.0` and `1.1` record:

- capture timestamp and connector version;
- project name, local path, and GUID;
- active sequence name, GUID, duration, frame size, and timebase;
- video and audio track order, name, ID, and mute state;
- each clip instance's display name, timeline in/out, source in/out, disabled state, project item name, and media path.

Schema `1.1` also records caption-track count plus `partial` and `issues`. `partial: true` means one or more clip instances could not be inspected; the remaining evidence is usable, but the missing scopes must be reported rather than silently treated as an empty track.

Times are decimal seconds. Track indices are zero-based, matching the Premiere API. Items are ordered by timeline start within each track.

The snapshot intentionally excludes frames, waveforms, transcript text, effects, keyframes, captions, markers, render state, and approval state. Those require separate evidence.

Project and media paths can expose names, clients, or private directory structure. Keep the original snapshot local and redact paths before sharing it.
