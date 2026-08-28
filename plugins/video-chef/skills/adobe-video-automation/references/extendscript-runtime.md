# ExtendScript and JavaScript Tools

Source: https://github.com/docsforadobe/javascript-tools-guide

Read this shared guide for ExtendScript language behavior, `$` globals, reflection, File and Folder operations, ScriptUI, BridgeTalk, localization, debugging, profiling, sockets, and cross-application messaging.

## Runtime rules

- Target the actual JavaScript engine supported by the installed application. Avoid unsupported modern syntax unless a tested transpilation step is part of the project.
- Normalize and validate paths for the host OS. Keep source projects and media immutable unless overwrite is explicitly authorized.
- Treat BridgeTalk and cross-application calls as asynchronous operations with timeouts and error handling.
- Use reflection to diagnose a live object mismatch, not to invent undocumented production behavior.
- Keep UI prompts minimal and avoid blocking headless or queued workflows unexpectedly.
- Do not log private paths, transcript contents, or project metadata beyond what the task needs.

The `Types-for-Adobe` repository can improve editor completion and static checking, but type declarations do not guarantee that the installed host exposes the same runtime surface.
