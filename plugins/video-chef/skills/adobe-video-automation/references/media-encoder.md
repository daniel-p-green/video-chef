# Adobe Media Encoder scripting

Source: https://github.com/docsforadobe/ame-scripting-guide

Use this guide when the requested workflow needs a real Media Encoder queue or cross-application render handoff rather than a direct `ffmpeg` export.

Resolve the source project or sequence, output preset, destination, collision behavior, and queue ownership before enqueueing. Use a unique review or delivery filename, subscribe to available status callbacks, record the job identifier, and wait for a terminal state. Do not treat queue submission as render completion.

After completion, confirm that the expected file—not an older file with the same name—was written. Probe and decode it independently, then perform required visual and sound review. If the guide surface differs from the installed AME version, verify against the live application before relying on it for batch work.
