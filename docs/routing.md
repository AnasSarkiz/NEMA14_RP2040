# Accepted routing — service revision

Accepted copper is frozen in `artifacts/board.circuit.json`. Starting Freerouting/native-authorouter evidence is retained historically; the original SES replay is not claimed to reproduce this revised delivery. Motor/USB bay changes use explicit recorded grid-routing/manual repairs, then native/actual-CAM connectivity and clearances. Existing layer counts are retained. `index.circuit.json` must match saved delivery before publication.

Scripts under `scripts/` record bay trimming, routing, pour clearance/refill, holeless pour export and removal of actual unanchored ground splinters. The final source/CAM reports and manifest validate the resulting accepted copper. Do not regenerate copper from an old SES or run `autoroute` over the delivery and presume equivalence. Rerouting requires the full source, native connectivity, trace-width, all-layer actualCAM/drill, stencil/via and shorts checks again.

Source/current pin-net invariance and physical pad/pose checks preserve the electrical graph. USB mouth locations/pitch and motorheader drilling changed deliberately. No controlled impedance, USB/QSPI EMC, current-sharing thermal performance or hardware operation is established by geometric connectivity.
