# Public release verification

The release version comes from `package.json`. The unchanged `scripts/verify-publication.py` compares unauthenticated public Circuit JSON/native build, default Gerbers, actual mounting drills, the order-review package and pinned GitHub CAD/source files against the qualified board. The authoritative completed receipt is committed to `artifacts/publication-verification.json` after publication.

Public v1.11.0 is verified against 444 public files. Frozen board SHA-256: `67820851170068eb092c3b611949ce67218b58f1049365fd317e8c1a513645e6`. Published CAD/source files are pinned to GitHub revision `ed5a42fedf49ae1012bbe3681adaf78d160b3e43`. All 63 intended physical nets are connected; native DRC is 0 errors/0 warnings, and both default and order-review CAM pass. Four recognized nonpolar passive-orientation suggestions remain recorded with their actual native command status.

Historical schematic-baseline comparison fields remain as originally recorded. The direct current public-to-qualified-board comparison is true; the separate latest-Git proof preserves all source-component, port, net and source-trace arrays and all 13 oscillator geometries. See `artifacts/opposite-edge/verifier-baseline-context.json`.

Supplier/process/pickup approval, prototype bench qualification and rear motor/encoder mechanical evidence remain outstanding. No order or payment was submitted.
