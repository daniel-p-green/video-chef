# Sources and status

## Documentation set

The plugin routes across every scripting guide currently published by the docsforadobe organization:

| Product or runtime | Repository | Scope |
|---|---|---|
| Premiere Pro | https://github.com/docsforadobe/premiere-scripting-guide | Application, project, sequence, track, track item, marker, component, export, and related object model |
| After Effects | https://github.com/docsforadobe/after-effects-scripting-guide | Application, project, item, comp, layer, property, render queue, text, masks, and scripting object model |
| Adobe Media Encoder | https://github.com/docsforadobe/ame-scripting-guide | Encoder scripting guide and reference |
| Animate | https://github.com/docsforadobe/animate-scripting-guide | Application, document, timeline, window, and publishing automation |
| Illustrator | https://github.com/docsforadobe/illustrator-scripting-guide | Script execution and JavaScript object reference for artwork generation |
| ExtendScript / JavaScript Tools | https://github.com/docsforadobe/javascript-tools-guide | ExtendScript language features, File/Folder, ScriptUI, BridgeTalk, reflection, debugging, and localization |

Companion references:

- After Effects expressions: https://github.com/docsforadobe/after-effects-expression-reference
- Cross-application TypeScript declarations: https://github.com/docsforadobe/Types-for-Adobe
- After Effects native plugin SDK: https://github.com/docsforadobe/after-effects-plugin-guide
- Premiere Pro native plugin SDK: https://github.com/docsforadobe/premiere-plugin-guide

For current Premiere development, prefer Adobe's official UXP documentation at https://developer.adobe.com/premiere-pro/uxp/. Adobe identifies UXP as the current Premiere extensibility standard in supported versions; the docsforadobe Premiere guide remains valuable for legacy ExtendScript and CEP-era automation.

Native C++ plugin development is outside this skill. Use the plugin guides only when the user explicitly requests native plugin work.

## Authority and freshness

The Premiere and After Effects repositories identify themselves as community-supported documentation projects. The After Effects guide began with Adobe's CS6 scripting guide and has been updated by contributors; the repositories state that their content remains Adobe copyright. Treat these as high-value technical references, not as proof that a method is supported in every current application build.

Before using an API:

1. Check the exact page in the relevant repository or rendered docs site.
2. Check recent changelog or repository history when version drift matters.
3. Verify the object or method against the installed application with a read-only or isolated test.
4. If the guide and runtime disagree, trust observed runtime behavior for that installed version and report the discrepancy.

Type declarations improve authoring and discovery but do not prove runtime availability. Undocumented extras, command IDs, QE DOM, and helper libraries require an explicit compatibility caveat.
