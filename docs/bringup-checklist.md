# Bring-up and qualification — unperformed hardware tests

- [ ] Confirm actual motor revision, frontM3 depth/pattern, factory lead gauge/OD/material, winding pairs and HAR-001 continuity/color mapping before power. Measure crimp/splice/clamp pull retention and all worst-case gaps; qualify material certificates, temperatures and repeated servicing.
- [ ] Fabricator accepts finished header bores0.75±0.05 mm, plated USB slots, layer stack, IPC4761TypeVII exposed-pad vias and cap flatness. Inspect solder/tails/insulation; supplier approves every pickup/rotation/pin1/polarity preview.
- [ ] With motor disconnected, check shorts and insulation to motor/carrier; current-limit separate DATA5V andPD supplies. Check3V3, RP1V1 if applicable, every reset default and current consumption.
- [ ] Verify PD requests15V with an analyzer;5V fallback stays disabled. DATA port enumerates and ROM USB flash works; demonstrate application control and timeout. Preserve SWD/WCHdebug recovery. No USB programming measurement is currently claimed.
- [ ] Scope3V3,VM,LOGIC_IN,OE,ADCpin−VDD,host sense,STEP/ENABLE/SLEEP through all cable orders, removal,PD fallback/reset/brownout and fast collapse. Enforce exact pin limits and no backfeed/ghost powering/unintended steps; revise supervision/clamps if required.
- [ ] Measure rail/load/current/ripple/startup. CH32 verify exact Holtek thermal/line/load margins under worst USB/motor firmware load. RP obtain biased/aged effectiveC and verify LC/load-transient stability and inductor current/temperature, including startup/short behavior.
- [ ] Attach motor with outputs disabled; establish ≥1ms sleep-release delay and ≥1µs pulse timing. Scope both phase/sense waveforms across microsteps/decay/supply/temperature. Peak winding current≤0.40A including measurement uncertainty; formula-only value is not qualification.
- [ ] Establish machine inertia/speed/backdrive energy, scope worst regenerative stops and unplug scenarios. PD may not sink. Bus/logic stay within operating/transient limits; design a qualified braking/clamp subsystem if bulk/TVS cannot absorb energy. Do not hot-unplug motor.
- [ ] Thermal soak mounted motor atworst intended duty/ambient: A4988/sense/CH224feed/Holtek or buck/inductor/bulk/PCB/PHcontacts/cables/insulation/carrier. MotorClassB130°C does not qualify80°C USB cables or85°C IC ambient limits.
- [ ] Simultaneously fit selected Tensility cables, measure shoulder/metal registration/gaps/bends, verify plug insertion/removal and10mm motorplug withdrawal. Check hardware/preload/host shaft engagement/structure/vibration and cable strain relief.

Record equipment, revision/hash, measured waveforms/limits/uncertainty and disposition for each test. All boxes remain unperformed until actual records exist.

The inward JST revision and required body-edge/plug-access checks are documented in [inside-board-jst](inside-board-jst.md). Fabricate only from its current manifest-bound artifacts.

## Outer-layer routing revision qualification

- Review the exact current native and actual-CAM reports in `docs/outer-power-routing.md`; retain the documented main widths and bounded pin escapes when changing routes.
- Confirm minimum copper/plating and all Type VI/Type VII/fine-drill process requirements against the actual fabrication order. Inspect barrel/SMT/stencil coupons and every supplier placement orientation.
- Measure both effective sense/return resistances and both peak winding currents. Record phase balance/torque across microsteps, decay and mounted temperature; the component-only current formula excludes PCB parasitics and low-VREF driver accuracy.
- Test USB ROM programming and enumeration, PD 15 V negotiation, power-order/brownout/reset behavior, regeneration/hot-plug clamp energy, mounted temperatures, and full motor/carrier/harness/two-plug fit. None of these hardware tests has been performed.
