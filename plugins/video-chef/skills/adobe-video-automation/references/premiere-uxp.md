# Premiere Pro UXP

Primary sources:

- https://developer.adobe.com/premiere-pro/uxp/
- https://developer.adobe.com/premiere-pro/uxp/ppro_reference/
- https://developer.adobe.com/premiere-pro/uxp/changelog/

Adobe identifies UXP as Premiere's current extensibility standard beginning with the official Premiere Pro 25.6 release. Use UXP for new panels and commands when the installed version supports the required DOM. Check each member's minimum-version tag and the current changelog.

UXP is not a browser. Use only supported HTML, CSS, and UXP APIs. Declare the narrowest required permissions; external process launch and filesystem access are constrained by the plugin manifest. Treat Premiere DOM methods as asynchronous where documented, obtain the active project and sequence through the supported API, and await mutations before verifying the result.

Do not silently port synchronous ExtendScript assumptions into UXP. When the current UXP DOM lacks a required operation, document the gap and choose among a legacy ExtendScript bridge, a user-visible manual step, or a different supported workflow. Do not fall back to QE without explicitly naming the compatibility risk.
