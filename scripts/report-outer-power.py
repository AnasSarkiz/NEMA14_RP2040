"""Document current source-bound main widths, actual CAM and retained transitions."""
import json,pathlib,hashlib,datetime
root=pathlib.Path(__file__).resolve().parents[1];read=lambda f:json.loads((root/f).read_text());source=root/'artifacts/board.circuit.json';sha=hashlib.sha256(source.read_bytes()).hexdigest();policy=read('artifacts/validation/service-outer-power-policy.json');cam=read('artifacts/validation/service-outer-power-cam.json');width=read('artifacts/trace-width-review.json');assert policy['checksPassed']and policy['sha256']==sha and cam['checksPassed']and cam['source_sha256']==sha and width['sha256']==sha
name=read('package.json')['name'];text=f'''# Outer-layer motor and 15 V routing review — {name}

Current saved-board SHA256: `{sha}`.

The old RP2040 review found motor wire segments and a long 15 V route on inner2, with main phase widths below the 0.45 mm source setting. Those main-width and wire-layer violations are corrected. Both boards retain the 35 × 35 mm outline and their existing layer counts. Main motor phases and PD_VBUS use **at least 0.45 mm on top/bottom only**. Sense-current wires use at least 0.30 mm on top/bottom. Ordinary motor/power/sense barrels have at least 0.25 mm finished drills; through-barrel annuli also appear on inner layers, but there are no motor/PD/sense wire segments there.

`npm run build` enforces the saved-copper rule. `npm run check:manufacturing` also enforces it, parses the actual Gerber/drill ZIP, and verifies approved wire strips against exported copper. The checks distinguish native pin escapes, resistor-only leaves and main routes. They fail on an inner-layer power wire or an unproved width reduction; nominal JSX settings alone cannot establish compliance.

| Net | Main minimum (mm) | Wire layers | Main branched length (mm) | Total routing vias across all branches |
|---|---:|---|---:|---:|
'''
for r in policy['nets']:text+=f"| {r['net']} | {r['mainMinimumWidthMm']:.2f} | {', '.join(r['wireLayers'])} | {r['mainBranchedLengthMm']:.2f} | {r['totalThroughVias']} |\n"
text+='''
Lengths and counts above cover all routed branches. They are not a series-path resistance or a count of vias carrying the entire inlet current. The following minimum available transitions come from independently parsed copper islands and actual plated drill barrels. A native plated connector pin is not counted as a routing via. This graph counts available layer changes; it does not establish current division or temperature.

| Net | Native path | Minimum available routing-via transitions |
|---|---|---:|
'''
for p in cam['actual_minimum_via_paths']:text+=f"| {p['net']} | {p['from']} → {p['to']} | {p['minimumAvailableThroughViaTransitions']} |\n"
text+='''
The retained phase vias are a disclosed compromise of the exact fine-pitch A4988 footprint, fixed connector pin order and dense 35 mm board. They are reviewed standard barrels rather than fine quiet-net vias. Through-via parasitics and plated-barrel quality still require fabrication and hardware qualification. The designs do not meet a zero-phase-via target; a strict zero-via requirement would require another placement/routing revision.

Short native driver/USB pin escapes remain narrower than the main routes. Each is positively checked for the exact native starting pin, width, maximum length and a complete joint to either a standard 0.25/0.50 mm barrel or a full-width top-layer route. A barrel is removed only when the complete escape endcap is already covered by top main copper, every native power pad remains in one physical island and every remaining power trace/via remains anchored. The resistor-only 0.16 mm leaves are independently proven by removing their exact copper records: only the resistor input separates while both inlet and driver supply pins remain together.

| Native escape | Width (mm) | Actual / maximum length (mm) | End connection |
|---|---:|---:|---|
'''
for p in policy['boundedExceptions']:
 if p['kind']=='bounded_native_pin_escape':text+=f"| {p['reference']}.{p['pin']} | {p['widthMm']:.2f} | {p['lengthMm']:.3f} / {p['maximumLengthMm']:.2f} | {p['endConnectionKind']} |\n"
text+='''
The narrow OUT1B escape is 0.20 mm; other listed driver escapes are 0.30 mm. Driver escapes are bounded to 2 mm and USB VBUS escapes to 1.25 mm. The 0.40 A winding and 0.75 A PD arithmetic screens assume external copper at least 35 µm and barrel plating at least 20 µm. An IPC-2221 estimate below the 30 °C screen does not verify a mounted temperature, pulse current, regeneration or a fabrication stackup.

## Current-sense parasitics and remaining electrical qualification

The A4988 sense pins carry winding current. The nominal 0.350765 A and component-only 0.379245 A high-corner formulas use the 0.24 Ω shunts alone; they exclude PCB sense/return resistance, driver accuracy at the selected low VREF and the measured supply/temperature corners. Source-derived sums below conservatively count every trace record and via in each sense net. Overlapping pad/trace copper and current sharing are not modeled, so these are screening data rather than predicted measured phase currents.

| Sense net | Sum of trace resistance at 20 °C (mΩ) | Sum of ideal barrel resistance (mΩ) | Total / nominal 240 mΩ shunt |
|---|---:|---:|---:|
'''
for net in ['SENSE1','SENSE2']:
 tr=sum(s['resistanceAt20CMilliohm']for s in width['segments']if s['net']==net);vr=sum(v['estimatedBarrelResistanceMilliohm']for v in width['viaReview']if v['net']==net);text+=f'| {net} | {tr:.3f} | {vr:.3f} | {(tr+vr)/240*100:.2f}% |\n'
text+='''
Measure effective shunt/sense/return resistance and peak current in both phases across decay modes, microsteps and mounted temperature. The RP2040 sense paths have larger, unequal arithmetic parasitics; qualify current balance and torque and revise their placement/routing if the measured imbalance is unacceptable. Do not compensate shunt values from unverified copper arithmetic. The A4988 has one shared analog VREF and no per-phase current register. Set and verify both winding currents below the motor's 0.40 A rating including measurement uncertainty and driver error; an unacceptable phase imbalance requires a hardware routing revision.

New quiet-net fanouts use ordinary off-pad 0.20/0.40 mm vias. `ordinary_via_process.csv` specifies each drill, annulus, aspect ratio and SMT-land margin. Close off-pad barrels require Type VI resin fill and mask cover; the exposed-pad vias retain the separate Type VII copper-capped requirements. Obtain supplier capability, process pricing and coupon/X-ray acceptance before ordering. Native and actual CAM checks reject ordinary drill/paste or drill/SMT intersections; process requirements are not claims of a manufactured result.

Both USB openings still face the same edge, fitted components remain on top, and the entire JST housing/mating housing remains inside the PCB with the documented assembly-tolerance screen. All native component/pad/hole/model geometry is unchanged by this copper revision. The completed mechanical review is rebound only after proving that physical geometry equivalence. The disclosed generic JST-post model discrepancy and supplier pickup/rotation approval remain open.

Required hardware tests remain unperformed: winding current/balance/torque, USB ROM programming and enumeration, 15 V PD behavior, all power orders and brownout/reset, hot-plug and regenerative clamp energy, mounted temperatures, and actual carrier/harness/two-cable fit and retention. This review does not authorize production release.
'''
(root/'docs/outer-power-routing.md').write_text(text)
for filename in ['engineering-review.md','inside-board-jst.md','routing.md','validation.md']:
 p=root/'docs'/filename;s=p.read_text();s=s.replace('Main motor/sense routing stays at least0.279 mm wide.', 'Main motor and 15 V routing is at least 0.45 mm on the outer layers; sense-current routing is at least 0.30 mm on the outer layers.');marker='\n## Verified outer-layer routing revision\n';s=s.split(marker)[0];s+=marker+'\nSee [outer-power-routing.md](outer-power-routing.md) for the current exact widths, bounded pin/leaf exceptions, actual plated-drill path counts and quantified sense-path parasitics. The saved-copper build rule and independently parsed CAM strip/net/clearance checks pass for the bound source. Retained phase vias and hardware/process qualification are explicitly documented.\n';p.write_text(s)
p=root/'docs/bringup-checklist.md';s=p.read_text();marker='\n## Outer-layer routing revision qualification\n';s=s.split(marker)[0];s+=marker+'''\n- Review the exact current native and actual-CAM reports in `docs/outer-power-routing.md`; retain the documented main widths and bounded pin escapes when changing routes.\n- Confirm minimum copper/plating and all Type VI/Type VII/fine-drill process requirements against the actual fabrication order. Inspect barrel/SMT/stencil coupons and every supplier placement orientation.\n- Measure both effective sense/return resistances and both peak winding currents. Record phase balance/torque across microsteps, decay and mounted temperature; the component-only current formula excludes PCB parasitics and low-VREF driver accuracy.\n- Test USB ROM programming and enumeration, PD 15 V negotiation, power-order/brownout/reset behavior, regeneration/hot-plug clamp energy, mounted temperatures, and full motor/carrier/harness/two-plug fit. None of these hardware tests has been performed.\n''';p.write_text(s)
print(name,'documented actual outer-power routing and retained qualification gates')
