## Current v1.12.0 assembly preview

The default public preview is `assembly.circuit.json`; fabrication remains `index.circuit.json`. `scripts/publish-tscircuit.sh --bounded-upload` stages and builds both saved JSON files, pins supplier CAD URLs to the pushed source revision, compacts the staged standalone assembly JSON and verifies parsed-record preservation. Upload batches are bounded by both encoded bytes and 24 files. After upload, `verify-publication.py` checks fabrication and evidence, while `verify-assembly-publication.py` separately checks the actual public default preview. No rerouting occurs during publication. See [the current verification receipt](publication-verification.md) and [assembly limits](top-assembly.md). GLB and interactive local-viewer files are stored in Git; the registry preview renders the native assembly JSON.

> Historical baseline document: this predates the opposite-edge v1.11.0 draft. See [current draft and blockers](opposite-edge-review.md) for current evidence.

# Publishing the validated prototype

`npm run publish:tscircuit` gates the frozen saved board, default manufacturing archive and JLCPCB review package before publication. The package includes the saved Circuit JSON and matching native CLI build; publishing preserves routing and changes only supplier CAD URLs to the validated GitHub commit.

The default Gerber archive applies the reviewed assembly, stencil and silkscreen policies. Upstream CLI output remains a diagnostic file. See [engineering fixes](engineering-fixes.md) and the hash-bound validation receipts for current results.

Supplier placement/process approval, verified stackup, firmware/bench qualification and rear motor mounting evidence remain pending. A prototype publication does not approve a manufacturing order.
