# Saved supplier-footprint routing

The latest native tscircuit autorouter was run and its result is saved as `artifacts/autorouted.circuit.json`. Remaining violations required the authorized Freerouting fallback. `scripts/export-supplier-router.py` exports exact imported polygon, rectangle, pill and circle pads to `supplier-input.dsn`; Freerouting 2.0.1 output is saved in `supplier-board.ses`. `scripts/import-supplier-session.py supplier` converts that session without replacing supplier footprints.

The CH32 board uses two copper layers. The RP2040 board uses top / inner1 ground / inner2 signals / bottom, with no inner1 signal tracks. RP2040 ground fills have 0.20 mm clearance and 0.35 mm edge margin. Ordinary fallback vias are 0.50/0.25 mm. Two RP2040 QSPI escape vias are 0.40/0.20 mm. Only grounded exposed-pad thermal vias may sit inside pads. All fitted components and paste are on top; through-hole USB shield joints require soldering.

Selected final PCB changes from the fallback session are recorded in `supplier-routing-adjustments.json`. These include thermal-pad contact segments, and on RP2040 a 0.10 mm C_DV50 move, neighboring V1V1/QSPI_SD3 trace adjustments and the completed QSPI_SD0 route. No native supplier land pattern was changed. `replay-supplier-adjustments.py` checks each expected before-record before applying the saved adjustment set.

Validate the final `board.circuit.json` with `npm run check`, the native-geometry `verify-connectivity.py`, `tsci check`, and all-layer 100 pixels/mm Gerber shorts analysis. These checks do not establish controlled impedance, EMC, manufacturing fit or tested hardware operation.
