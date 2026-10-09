# Full JST housing inside the PCB

The former pin-row placement at Y-16.4 mm left the native header housing beyond the 35 mm board. The row is now at (1.7, −14.1) mm, rotation0°, on top. Placement must include the housing depth, not just the four holes.

The full imported B4B-PH-K-S(LF)(SN) housing extends to Y−17.1 mm: **0.4 mm nominal inside** the Y−17.5 mm edge. The PHR-4 mating-housing envelope extends to Y−17.0 mm: 0.5 mm nominal inside. The mechanical review uses unchanged native supplier OBJ/STEP coordinates and separately modeled mating housing; no housing was clipped to obtain this fit. The finished bore remains 0.75±0.05 mm, pad diameter1.6 mm and pin pitch2 mm.

The declared ±0.2 mm outline and ±0.1 mm placement allowances leave 0.1 mm nominal header margin and0.2 mm mating-envelope margin. These are procurement/assembly requirements, not measured factory tolerances. Manufacturer plastic dimensional bounds, generic square-post CAD discrepancy and an assembled fit/coupon test remain qualification gates. Reject any sample whose actual body extends beyond the outline.

The 35×35×1.6 mm outline, layer count, mounting-hole locations, top assembly, same-edge USB mouths and motor pin identities are retained. Nearby driver parts and local copper were rearranged to preserve clearance and ordinary-via access. The three grounded exposed-pad vias remain filled/capped; RP2040 also retains its C_USB filled/capped via. Additional ordinary vias must be tented; no open via under a solder pad is permitted.

Main motor/sense routing stays at least0.279 mm wide. The explicitly bounded 0.20 mm OUT1B fanout to a standard0.25/0.50 mm via is ≤2 mm long and independently checked for the0.40 A/30°C copper-rise screen. That exception does not reduce the main-route floor. Sense trace resistance/ground offsets and mounted phase current still require hardware qualification. RP2040 retains the previously reviewed regulator bootstrap placement and copper; biased capacitance, converter stability and switching behavior remain unmeasured.

See `artifacts/validation/service-motor-inside-board.json` for exact native-model bounds, `artifacts/mechanical/mechanical-review.json` for assembled component/plug/wire/fastener access and `artifacts/validation/engineering-review-manifest.json` for current acceptance artifacts and hashes. Only reports bound to the final saved circuit JSON validate the release. Routing-workflow intermediate reports are diagnostic history.

After reflow, hand solder the top header, trim/insulate tails, seat the temperature-rated barrier and carrier supports, fit the keyed PHR-4 and retain its service loop in the carrier clamp. Inspect body-to-edge margin, neighboring components and ≥10 mm vertical withdrawal access with actual parts before power. Motor pin1 BlackA+, pin2 GreenA−, pin3 RedB+, pin4 BlueB−; verify continuity before energizing.

Winding current, USB/PD/programming, power-order/brownout, regeneration, mounted temperatures and physical fit remain unperformed hardware tests. Offline source/CAM checks do not establish production readiness.

RP2040 uses an additional ordinary 0.20/0.40 mm ground via between the R_REF_L lands. It is outside both solder pads, with 0.150126 mm nominal land clearance, and must be tented. This preserves the existing 8:1 drill-process requirement and adds no filled/capped via. The assembly remains conditional on supplier process acceptance.
