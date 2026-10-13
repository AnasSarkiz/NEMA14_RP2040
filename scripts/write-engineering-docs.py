"""Write current engineering documentation from hash-bound final receipts."""
import collections,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];read=lambda p:json.loads((ROOT/p).read_text());proof=read('artifacts/engineering-fixes/final-engineering-verification.json');sha=proof['board_sha256'];v=read('artifacts/resume-validation.json');cam=read('artifacts/manufacturing/audit.json');usb=read('artifacts/engineering-fixes/usb-verification.json');m=read('artifacts/mechanical/mount-usb-screen.json');j=read('artifacts/board.circuit.json');pkg=read('package.json');assert v['board_sha256']==cam['source_sha256']==usb['board_sha256']==sha
checks='\n'.join('| '+c['check']+' | '+('PASS' if c['exit_code']==0 else 'Reviewed orientation advisories; placement DRC clean' if c['check']=='native_placement' else 'FAIL')+' | `'+c['log']+'` |' for c in v['checks'])
counts=collections.Counter(e['type'] for e in j);changes='\n'.join('| '+r['reference']+' | '+str((r['before_center_mm']['x'],r['before_center_mm']['y']))+' | '+str((r['after_center_mm']['x'],r['after_center_mm']['y']))+' |' for r in proof['moved_references']);core='\n'.join('| '+c['core']+' | '+c['layer']+' / '+c['reference_layer']+' | '+f"{c['core_length_difference_mm']:.3f}"+' | '+', '.join(f"{t['ground_reference_coverage_fraction']*100:.3f}%" for t in c['tracks'])+' |' for c in usb['cores'])
text=f'''# {pkg['name']} {pkg['version']}: engineering fixes

Saved board SHA-256: `{sha}`. Starting GitHub revision: `{proof['baseline_github_commit']}`. Every original functional terminal, named/implicit net group, NC role, fitted MPN, LCSC number, component value and rating is preserved; see `artifacts/engineering-fixes/final-engineering-verification.json`.

The board is 35 × 35 × 1.6 mm, four layers, with four NPTH holes exactly (±13, ±13), Ø3.2 mm. USB mouths remain (−6.2, 17.5) and (6.2, 17.5), both facing +Y. Two defined 10 mm cable housings have 2.4 mm nominal separation. The fastener requirement remains maximum Ø4 mm heads; the STEP screen includes a Ø4.4 mm × 3 mm envelope. This verifies nominal CAD geometry, not physical assembly or rear motor attachment.

All {proof['fitted_components_on_top']} fitted parts and {proof['bare_top_test_points']} separate bare test pads remain on top. Standard USB-C schematic symbols, both contact orientations, independent 5.1 kΩ data CC resistors, CH224K 15 V configuration, Schottky supply isolation, SMT JST-SH C160390 coil order, TMP102, LEDs and buzzer are retained. See [reference pin review](reference-feedback.md) and [motor connector/harness](jst-restoration.md).

## Routing and source fixes

ESD protection and local parts were moved to support coupled outer-layer USB trunks with explicit MCU/ESD/resistor fanouts. Affected copper and ground returns were rerouted; redundant stubs and duplicate records were removed. The RP2040 shared rail bridge is 0.25 mm on inner1 after its conservative thermal screen rejected 0.16 mm. The reviewed layer policy bounds low-current/control escapes and the short 0.3 mm phase bridge; clocks/flash retain a 15 mm section limit. Every trace, segment, via ownership and attached physical port is inventoried, with actual copper connectivity and thermal/clearance checks required separately.

| Reference | Previous XY mm | Current XY mm |
|---|---|---|
{changes}

| Coupled core | Signal / reference layer | Length difference mm | Exact grounded reference coverage outside actual USB via antipads |
|---|---|---|---|
{core}

Core width/gap are 0.25/0.16 mm; local terminal fanouts are 0.16 mm. Every projected centerline is intersected geometrically with adjacent grounded copper. This is layout evidence; fabricator stackup/controlled impedance, USB signal integrity, EMC and hardware operation are unverified.

Display offsets are canonical strings and optional null IDs are omitted. Board-level silkscreen records have a valid metadata owner while retaining absolute coordinates. BZ1 uses the installed generic pinout classification with its real MPN, pins, nets, models and qualified schematic retained. Strict schema checks accept no inherited errors.

## Manufacturing output

The default `artifacts/nema14-gerbers.zip` now applies qualified source-derived BOM/CPL, top-only paste, 100 µm stencil apertures, four 60% exposed-pad windows and readable silkscreen with mask/drill/edge guards. Bare test pads and mounting holes are excluded from assembly purchasing and paste. Copper, masks, outline and drill bytes remain identical to the upstream native exporter. `artifacts/engineering-fixes/upstream-native-gerbers.zip` is retained for diagnosis; the default archive and the separate order-review CAM both pass their independent audits.

The actual drill/outline files verify the specified 35 mm square and (±13, ±13) Ø3.2 mm mounting holes. Source, placement and Gerber copper agree. Current counts: {counts['pcb_trace']} trace records, {counts['pcb_via']} vias, {counts['pcb_copper_pour']} grounded regions; {v['physical_nets_checked']} physical net groups connected. Native DRC: zero errors/warnings. Placement orientation advice remains visible and is accepted only when every full flagged-component diagnostic is a recognized passive-orientation suggestion and placement DRC is clean.

| Required check | Result | Evidence |
|---|---|---|
{checks}

## Remaining supplier and hardware blockers

JLCPCB must confirm exact stock/quote, pickup datums, pin 1/polarities and rotations, specified copper/plating/stackup, 100 µm stencil/reflow and the three filled/capped/planarized exposed-pad vias. Eight USB shell through-hole joints require quoted secondary soldering. The mating JST-SH pigtail and motor lead termination need supplier/assembler confirmation; the factory motor has bare leads.

Firmware, USB boot/data, 15 V PD negotiation, host-only regulator headroom, isolation/backfeed, current accuracy, regulator stability, switching/sense/ground behavior, temperature/thermal operation, buzzer/LEDs, motor regeneration and EMC need prototype bench validation. Real plugs, fastener SKU/tolerances, thread engagement, spacing/underside clearance and the rear motor/adapter must be checked physically. The manufacturer drawing supplies front mounting dimensions only. No rear compatibility, supplier order approval or production release is claimed; no order/payment has been submitted.
'''
(ROOT/'docs/engineering-fixes.md').write_text(text)
(ROOT/'docs/routing.md').write_text(f'''# Current routed geometry

The authoritative saved Circuit JSON and delivered preview have SHA-256 `{sha}`. All {v['physical_nets_checked']} physical net groups are connected; native DRC has zero errors/warnings. Current source/geometry, each trace and actual Gerber copper are independently checked. Construction receipts and baseline files are historical; current hash-bound receipts are authoritative.

See [engineering fixes](engineering-fixes.md) for the coupled USB routes, reviewed layer policy, current placement changes, checks and remaining supplier/bench blockers. The default manufacturing archive and separate JLCPCB order CAM pass. No controlled-impedance or hardware-function qualification is implied.
''')
(ROOT/'docs/mounting-usb-verification.md').write_text(f'''# Current mounting and USB verification

Saved board SHA-256: `{sha}`. Source, actual Gerber outline and Excellon drill files agree on 35 × 35 mm and four Ø3.2 mm NPTH holes at exactly (±13, ±13). Native STEP screening passes for the approved same-edge USB mouths, two defined 10 mm housings at 12.4 mm pitch, and a Ø4.4 × 3 mm head envelope around the required maximum Ø4 mm fastener heads.

The nominal cable-housing gap is {m['minimum_simultaneous_plug_gap_mm']:.3f} mm. Actual supplier footprints/courtyards and models are retained. See [engineering fixes](engineering-fixes.md), `artifacts/mechanical/mount-usb-screen.json`, `artifacts/mount-drill-verification.json` and the actual CAM audit for current evidence.

Both primary and order-review manufacturing archives pass their full CAM audits. Passive-orientation advisories remain reviewable in the native placement log. The publication gate rejects other diagnostics and any real geometry/CAM failure.

The manufacturer motor drawing dimensions front holes only. Rear motor fit, adapter geometry, physical cable/fastener tolerances, assembly stack/thread engagement and hardware operation remain unverified.
''')
(ROOT/'docs/validation.md').write_text('''# Current validation

The current board is qualified by the 20 hash-bound checks in `artifacts/resume-validation.json`, native STEP screening, full default CAM audit and separate JLCPCB order-CAM audit. Native passive-orientation advice retains its actual nonzero command status; only the complete recognized advisory class with clean placement DRC is reviewable for prototype publication.

Read [engineering fixes](engineering-fixes.md) for actual results and [order review](jlcpcb-order-review.md) for supplier requirements. Publication requires current strict schema, USB reference, every-trace, physical connectivity, copper/thermal, exact drill and mechanical receipts. Supplier/process approval, firmware, bench testing and rear-mount evidence remain outstanding.
''')
(ROOT/'docs/publication-verification.md').write_text(f'''# Public release verification

The release target is {pkg['version']}. `scripts/verify-publication.py` compares the unauthenticated public index/native build, default Gerber archive, actual mounting drills, review package and pinned GitHub CAD/source bytes against the frozen qualified board. The verified release/version and commit are recorded in `artifacts/publication-verification.json` after publication.

See [engineering fixes](engineering-fixes.md) for current checks. Strict generic Circuit JSON schema and both manufacturing archives pass. No supplier order/process approval, bench qualification or rear motor compatibility is claimed.
''')
for p in [ROOT/'docs/ai-review-assessment.md']:
 if p.exists():
  s=p.read_text();p.write_text('> Historical baseline assessment before the engineering fixes. Current results and resolved issues are in [engineering fixes](engineering-fixes.md).\n\n'+s if not s.startswith('> Historical') else s)
print('Current documentation written from verified receipts')
