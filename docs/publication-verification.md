# Public saved-layout verification

Version **1.3.0** of [NEMA14_RP2040](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040) publishes the same-edge USB layout and required DIN 920 head envelope described in [mounting and USB verification](mounting-usb-verification.md).

After uploading, run `python3 scripts/verify-publication.py` to retrieve the finalized public release without authentication. The resulting `artifacts/publication-verification.json` records the release ID, revision, public page status, hashes and verification time. The previous 1.2.0 receipt is archived in `artifacts/publication-history/1.2.0.json`; it does not qualify this geometry.

Verification compares public `index.circuit.json` and `dist/index/circuit.json` against the reviewed board, allowing only revision-pinned CAD URL metadata. It checks the exact 35 × 35 mm outline, same +Y USB mouths, required head/plug geometry, actual metric Ø3.2 mm NPTH coordinates (±13, ±13), byte-identical Gerber archive, native USB STEP, and published mechanical/CAM evidence. The stage verifies the saved JSON build before upload; the independent public read verifies the files actually delivered.

Publication preserves the complete CAM **FAIL**, passive-orientation suggestions, untested hardware status and unverified rear-motor fit. It is a prototype publication and does not authorize fabrication or assembly.
