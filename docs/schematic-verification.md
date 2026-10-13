# Five-sheet schematic verification

The qualified schematic uses standard USB-C symbols and five functional A4 landscape sheets. The current independent geometric/ERC analysis checks 88 components, 321 physical pins, 63 connected source nets and 33 explicitly unused pins. Native schematic-placement diagnostics are empty.

The analysis checks orthogonal conductors, label anchors, complete physical-pin coverage, named-net connectivity, distinct-net isolation, marked crossings/junctions and A4 bounds. The two JST mechanical hold-down pads are explicit NC roles and are omitted from the electrical symbol. The complete vector drawing is `artifacts/schematic-a4.pdf`; each sheet also has a native SVG.

Current board SHA-256 is recorded in `artifacts/schematic-redesign/analysis.json`. See [engineering fixes](engineering-fixes.md) for the source/routing qualification and remaining supplier/bench blockers.
