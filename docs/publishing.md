> Historical baseline document: this predates the opposite-edge v1.11.0 draft. See [current draft and blockers](opposite-edge-review.md) for current evidence.

# Publishing the validated prototype

`npm run publish:tscircuit` gates the frozen saved board, default manufacturing archive and JLCPCB review package before publication. The package includes the saved Circuit JSON and matching native CLI build; publishing preserves routing and changes only supplier CAD URLs to the validated GitHub commit.

The default Gerber archive applies the reviewed assembly, stencil and silkscreen policies. Upstream CLI output remains a diagnostic file. See [engineering fixes](engineering-fixes.md) and the hash-bound validation receipts for current results.

Supplier placement/process approval, verified stackup, firmware/bench qualification and rear motor mounting evidence remain pending. A prototype publication does not approve a manufacturing order.
