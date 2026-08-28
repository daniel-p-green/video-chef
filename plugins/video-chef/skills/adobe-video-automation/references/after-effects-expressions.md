# After Effects expressions

Source: https://github.com/docsforadobe/after-effects-expression-reference

Use this companion when code runs as an expression on a property rather than as an ExtendScript automation. Expressions are evaluated inside the project and have different objects, performance constraints, and side-effect rules.

Check the exact property dimensionality and units; comp, layer, and footage coordinate spaces; time and frame conversion; interpolation; vector math; text selectors; path operations; and expression-engine compatibility. Avoid per-frame work that scales poorly across many layers. After applying an expression, scan for expression errors and render a representative range.

Do not copy an expression API into an ExtendScript file or assume an ExtendScript object is available inside an expression.
