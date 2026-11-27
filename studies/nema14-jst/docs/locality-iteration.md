# NEMA14 JST placement and routing iteration

This is a bounded top-side engineering iteration from draft PR #2's original commit `a79d7cf3f1503c46a32e8ff0c9fb1e4bf2aed88f`. The outline, USB poses, connector pose, bottom encoder, four screw reserves, footprints, parts and electrical netlist remain fixed. All intended fitted components remain on the top. A smaller distance or passing placement target does not establish routed DRC, a low-inductance loop, physical Kelvin pickup, or hardware operation.

## Electrical priority and evidence

The original 59 numerical distance targets are unchanged. Risk ranking is additional engineering judgment. The following manufacturer guidance determines the priorities; it does not supply the study's millimetre thresholds.

| Priority | Circuit | Reason and primary evidence |
| --- | --- | --- |
| P0 | Driver supply, charge pump, regulation and sense returns | [Allegro A4988, p. 12](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf#page=12) places the star ground near the exposed pad, ceramic bypass ahead of bulk, and short sense connections with thick, low-impedance returns. Pin-1 proximity alone is insufficient. |
| P0 | Inline shunts and INA240 supply | [TI INA240, §§9.3.2, 10.1, 11; pp. 23–24](https://www.ti.com/lit/ds/symlink/ina240.pdf#page=23) requires separate shunt Kelvin connections and local supply bypass. Winding-current copper before the pickup must not enter the sensed voltage. |
| P0 | Buck switching supply | [Diodes AP63203, p. 15](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf#page=15) calls for local VIN capacitors, substantial ground copper and ground-side vias. Small pin distances cannot prove the current loop or thermal path. |
| P1 | RP2040 decoupling and crystal | [Hardware design with RP2040, §§2.1.2–2.3](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf#page=8) places decoupling near power pins and keeps oscillator wiring short to control parasitic capacitance. |
| P1 | USB signal and return | [RP2040 §2.4.1, p. 12](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf#page=12) places 27 Ω resistors near the MCU and requires uninterrupted ground beneath USB traces. Its example track dimensions are not copied to this four-layer board: a fabricator stackup is required for impedance. [ST USBLC6-2, §2.3, p. 6](https://www.st.com/resource/en/datasheet/usblc6-2.pdf#page=6) also minimizes connector, supply and ground lead inductance. |
| P1 | ADC output filters | Keep the series-resistor/capacitor pair local to the ADC input and separate it from switching paths. This is an engineering noise/sampling screen, not a manufacturer numerical distance specification. |
| P1 | Flash and PD bypass | Flash boot integrity and the negotiated supply controller remain required electrical functions; retain their existing proximity limits. |
| P2 | Temperature bypass and coil span | This ranks distance-only screens. Motor copper width, current loops, protection and thermal checks remain release gates; a longer external winding path is not part of the Kelvin measurement when pickup is correct. |

The baseline 40 failures are grouped by target in [locality-priorities.json](../scripts/locality-priorities.json). Before/after counters, every distance and exact native source hashes are in [the iteration report](../artifacts/iteration-1/report.json).

## Selection and bounded work

Compatible courtyard slots were reassigned without changing physical parts or values. A bounded grid/fine-position search then used real native pad coordinates, full top courtyards and all four screw envelopes. The native keepout contact tolerance is included in the candidate filter. All original passing targets must remain passing. Every P0 pad separation must be no worse than baseline; integer search comparisons allow only 0.0002 mm of coordinate quantization, while native and independent clearance rules remain unchanged.

Higher-count candidates were rejected when they worsened power/bypass separations. Lower-priority tradeoffs remain visible in the report: for example C_XIN-to-crystal grows from about 3.580 to 6.420 mm, while C_XOUT falls from about 6.980 to 2.750 mm. The oscillator therefore remains blocked; one passing capacitor target does not qualify that circuit. Another trial cleared the nominal screw circle but was rejected by native keepout-contact DRC. None of those rejected trials replaces the accepted native source. These bounded searches do not prove that an adequate all-top layout is impossible.

A full SRJ diagnostic identified a trapped SDA pull-up escape. A reversible 180° resistor comparison retained the courtyard and all locality distances while clearing the early reachability failure; it was then tested through the native TSX entry point. This is an internal placement change, not a change to the USBs, connector or mounting geometry.

## Explicit return and Kelvin contracts

[critical-routing-contract.json](../src/critical-routing-contract.json) reserves 0.6 mm wide return paths from **R_SA.pin2 and R_SB.pin2** to the **U_DRV.EP** star region, using short top stubs, real through-via dimensions and inner1 corridors. The 5 mm path target is an engineering placement screen, not an Allegro limit. [check-critical-paths.py](../scripts/check-critical-paths.py) checks the actual pad IDs, board edge, four screw reserves, conflicting pads/copper, ceramic-before-bulk ordering, and source ground assignments. The saved report contains the exact planned paths and all-layer via-barrel envelopes. The router does not gain phantom copper from these reservations: post-route checking rejects unrelated copper in them.

Once copper exists, the same checker requires an actual >=0.6 mm GND wire path with physical vias from each resistor to the exposed pad. It verifies each named Kelvin branch touches its actual inline 50 mΩ shunt pad, checks layer-by-layer overlap with the corresponding winding power branch outside that pad, and tests branch continuity with actual plated vias. A source trace name or a via node without a physical barrel cannot pass these checks. A pad-cut topology test removes only the actual shunt-pad copper and requires the amplifier and winding conductor to disconnect; this remains meaningful when the router merges trace identities.

For scale, 1 mΩ of shared copper is 2% of a 50 mΩ shunt. At 0.4 A and gain 20, it adds 8 mV at the amplifier output. This is a sensitivity calculation, not an estimate of the present unbuilt board's copper resistance.

USB ground-reference checking projects the entire routed track width onto the adjacent GND layer. An empty routing output or absence of an actual GND pour fails the reference check. Differential impedance and thermal behavior remain separate unverified gates.

## Native routing diagnostics and limits

The source is tested with `tsci build controller.tsx --routing-disabled`; native DRC remains enabled. The production autoroute command retains the original locality gate, adds the star-return preflight, and requires independent physical connectivity and critical-path checks after any native routed output.

Isolated SRJ experiments use the installed native converter and autorouter 0.0.958, retain every real pad/hole/keepout obstacle, and preserve all board width, via and clearance values. Driver, Kelvin and USB experiments reduce only the requested terminal set. The full experiment retains all 78 connections. Each routing loop has a nominal 60-second budget; a synchronous solver step can overrun it. A separate shell cap of 90 seconds bounds the process. Checkpoints and external timeouts are reported rather than counted as completed routing. Repeats can differ, so observed timings are not performance benchmarks. No experimental copper is installed in `artifacts/final-source.circuit.json`.

The diagnostic converter preserves output copper geometry, represents coincident same-net via holes once as native materialization does, and records any per-trace source-association limitation at junction-only branches. Native geometry/clearance checks and independent polygonal physical connectivity are reported separately. The native source-association checks on this diagnostic translation are not equivalent to a fully materialized native CLI routed build. Missing ports on the deliberately omitted nets remain visible.

The independent checker uses actual pad/slot outlines, annular copper, physical via layers, all copper layers, board edges, screw keepouts, copper spacing, drill spacing and trace-to-hole clearance. Eleven regression cases verify that shared names or crossing coordinates do not bridge layers, a real via does, a wrong-layer via does not, and a 0.106 mm via gap fails the 0.15 mm rule. The additional Kelvin cases distinguish a pad-local pickup from a shared winding stub and a shared barrel beneath the pad. It is not a Gerber/CAM, impedance, fabrication or bench audit.

The current native source contains no routed traces or vias. Full routing, both star-return copper paths, all Kelvin pickups, USB ground reference/impedance, physical cable handling, rear motor/magnet clearance, thermal behavior and bench operation remain gates. PR #2 stays draft.

## Observed routing results

| Isolated scope | Requested SRJ connections physically joined, before → after | Independent copper spacing violations, before → after | Shorts, before → after |
| --- | --- | --- | --- |
| driver | 9/9 → 9/9 | 1 → 1 | 0 → 0 |
| kelvin | 14/14 → 14/14 | 2 → 1 | 0 → 0 |
| usb | 6/6 → 6/6 | 1 → 0 | 0 → 0 |

These are reduced routing problems. Full-board opens on omitted nets remain reported. Both full 78-connection attempts were incomplete; repeat wall-timeouts and exact SRJ-equivalence provenance are retained. All four after-Kelvin paths fail the actual-pad cut test, both 0.6 mm routed star returns remain unverified, and USB lacks a verified adjacent ground reference. No solved subset is a clean-board result.
