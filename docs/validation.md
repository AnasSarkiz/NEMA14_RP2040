> Historical baseline document: this predates the opposite-edge v1.11.0 draft. See [current draft and blockers](opposite-edge-review.md) for current evidence.

# Current validation

The current board is qualified by the 23 hash-bound checks in `artifacts/resume-validation.json`, native STEP screening, full default CAM audit and separate JLCPCB order-CAM audit. The installed native checker and its bundled CLI are reproducibly patched to calculate analytic circle-to-trace distance for circular keepouts; the upstream checker used the circle’s bounding rectangle. Package before/after hashes and positive/negative regression cases are retained in `artifacts/upright-revision/native-circle-checker.json` and `circle-checker-regression.json`. No clearance rule is lowered and no real diagnostic is suppressed. Native passive-orientation advice retains its actual nonzero command status; only the complete recognized advisory class with clean placement DRC is reviewable for prototype publication.

Read [engineering fixes](engineering-fixes.md) for actual results and [order review](jlcpcb-order-review.md) for supplier requirements. Publication requires current strict schema, USB reference, every-trace, physical connectivity, copper/thermal, exact drill and mechanical receipts. Supplier/process approval, firmware, bench testing and rear-mount evidence remain outstanding.
