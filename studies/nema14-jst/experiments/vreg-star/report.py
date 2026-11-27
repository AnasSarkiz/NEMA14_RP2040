"""Human review from final independently measured native output; no fabrication acceptance."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import html,hashlib
r=Path('artifacts/iteration-11');j=resolve_copper_nets(read(r/'final.circuit.json'));q=read(r/'verification.json');cli=read(r/'cli-replay.json');bound=read(r/'star-access-bound.json');nm,cs,pc,sps,pps,ps,ct=index(j);pads={e['pcb_port_id']:e for e in j if e['type']=='pcb_smtpad'};st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'};vreg=next(e for e in j if e['type']=='pcb_trace' and st[e['source_trace_id']]=='AUTHORED_VREG_BASELINE');stress=unary_union([LineString([(a['x'],a['y']),(z['x'],z['y'])]).buffer(.096,quad_segs=128) for a,z in zip(vreg['route'],vreg['route'][1:])]);key=vreg['subcircuit_connectivity_map_key'];gaps=[]
for e in pads.values():
 if e['layer']!='top':continue
 port=pps[e['pcb_port_id']]
 if sps[port['source_port_id']].get('subcircuit_connectivity_map_key')==key:continue
 n=next(('.'.join(k) for k,p in ps.items() if p['pcb_port_id']==e['pcb_port_id']),'unknown');gaps.append({'terminal':n,'stressed_copper_gap_mm':stress.distance(g.pad_shape(e))})
gaps.sort(key=lambda e:e['stressed_copper_gap_mm']);assert gaps[0]['stressed_copper_gap_mm']>=.15;body=read(r/'body-bounds.json');moved=[e for e in body['parts'] if e['part'] in ['C_VREG','C_VCP']];local=read(r/'final-locality.json');oldloc=read('artifacts/iteration-10/final-locality.json');keyrow=lambda e:tuple(e[k] for k in ['a','pa','b','pb']);previous={keyrow(e):e for e in oldloc['rows']};lost=[e for e in local['rows'] if previous[keyrow(e)]['pass'] and not e['pass']];assert not lost and sum(e['pass'] for e in local['rows'])==43;facts={'input_sha256':hashlib.sha256((r/'final.circuit.json').read_bytes()).hexdigest(),'VREG_stressed_foreign_SMT_gaps':gaps[:8],'moved_capacitor_body_bounds':moved,'minimum_body_screw_gap_mm':min(e['minimum_screw_reserve_xy_gap_mm'] for e in body['parts']),'minimum_plug_service_gap_mm':min(v for e in body['parts'] for v in e['plug_envelope_bounds_gaps_mm'].values()),'candidate_locality':{'before':43,'after':43,'total':59,'lost_previous_passes':lost},'native_routing_attempted':False};(r/'review-facts.json').write_text(json.dumps(facts,indent=2)+'\n')
report=f'''# NEMA14 JST VREG and original-hole star comparison

Separate candidate from4600e6b. **VREG's native positive-leg length gate is resolved; the two original-hole star-via tolerance failures remain blocked by the retained driver land pattern.** Accepted controller, earlier comparisons, main and original boards remain unchanged. This candidate is not promoted; no new routing stage, merge, order or outreach.

| Check | 4600e6b | Separate candidate |
| --- | --- | --- |
| VREG authored wire / native maximum | 2.605856 /1mm | **{q['VREG']['actual_wire_mm']:.9f} /1mm**, no override |
| True VREG pad-edge gap | 1.366017mm | **0.885474mm** |
| Native VREG length errors | 1 | **0** |
| Independent nominal shorts / spacing / courtyard conflicts | 0 /0 /0 | **0 /0 /0**,101 top courtyards |
| Full +20% width-stress shorts / spacing | 0 /0 | **0 /0** |
| Original-hole adjusted SMT / annular / inner-via failures | 2 /0 /0 | **2 /0 /0**, retained |
| Copper / vias / independent open nets | 44 /22 /59 | **44 /22 /59** |
| Candidate locality | 43/59 | **43/59**, no lost pass |
| Native port / style diagnostics | 300 /4 | **300 /4**, retained |

## Datasheet and native semantics confirmed first

[Allegro A4988 Rev8](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf), page10, requires0.22µF ceramic VREG decoupling to ground; the retained220nF part meets the nominal value. Pages12/18 call for heavy ground, the GND pins tied to the PAD ground plane, short sense traces and thick low-impedance star returns. No numeric1mm VREG limit was found. This does not qualify the unfinished ground-return loop.

Pinned Core0.0.2110 infers **1mm** through `Capacitor_getAutomaticMaxDecouplingTraceLength` for power-to-ground topology and propagates it through `getMaxLengthFromConnectedComponents` to `source_trace.max_length`. Pinned checks0.0.283 sum physical trace lengths by source, preferring trace records with both actual endpoint identities; the utility uses cached `trace_length` when present. The independent guard therefore recomputes that length from copper and rejects a falsified cache. No dependency patch, limit override, source splitting or owner reassignment is used. `semantics.json` records exact installed source hashes and the source-owned rules.

The native limit measures authored **wire centreline**, excluding access inside pads. At the old placement, even allowing two0.08mm end caps gives a necessary lower bound **1.206017mm**, still over1mm. Thus clipping the old route alone cannot solve it. The old1.366017mm number is pad-edge separation, not a complete wire-centreline bound once end caps are allowed.

The new single trace has both endpoints **inside their real pads**. Its actual wire is **{q['VREG']['actual_wire_mm']:.9f}mm**, and cached length matches an independent recomputation. Both real endpoint IDs and the direct two-port source with `max_length=1` are retained. Including straight access from both pad centres gives **{q['VREG']['complete_port_centre_path_including_pad_access_mm']:.9f}mm**, reported separately. This is a native positive-leg pass, not a claim that the whole decoupling loop or centre-to-centre path is≤1mm.

## Small placement and escape change

Only two top-side components move: **C_VREG(6.650,11.375,180°)→(7.200,11.350,180°)**, translation0.550568mm; **C_VCP(8.950,11.350,180°)→(9.100,11.600,90°)**, translation0.291548mm. No part, footprint, drill or board geometry changes. The bounded0.05mm/orthogonal-rotation two-cap search supplies placement choices; it is not a global minimum proof or a routed screen. Rotating C_VCP frees the required C_VREG space while retaining its4mm locality target. Courtyard, copper and body checks then independently qualify the selected pair.

The first nearest-pad direct route was rejected: it cleared MS1 by only0.092384mm nominal and0.076384mm stressed against0.15mm. Final wire starts0.015mm inside the real driver-pad tip, escapes outward0.050mm past that tip, then ends0.005mm inside both edges of the capacitor-pad corner. All coordinates derive from the fresh native transformed pads. No port annotation is assigned before a real pad/annulus contact check. Final VREG stressed SMT minimum is **{gaps[0]['stressed_copper_gap_mm']:.9f}mm** at **{gaps[0]['terminal']}**, using actual0.16mm and stressed0.192mm copper; all full-board width gates remain clean.

**43 other trace route arrays and all22 via whole records are exact**, including both validated CP paths, cleaned buzzer paths, four Kelvin branches and both0.60mm returns. Their four actual shunt-pad removal tests still pass with zero shared winding copper outside pads. Returns remain **4.891754 /4.752642mm**, including annulus access and two conducted barrels; upper-depth totals remain4.928754 /4.789642mm. Native source/net/pin contract and1mm VREG maximum are exact. All29 driver SMT pad records are exact. Both USB poses, selected side-facing JST, bottom encoder, top DNP caps, four physical screw reserves and35mm/four-layer/1.6mm envelope remain fixed.

Supplier OBJ bounds are freshly transformed and hash-checked for69 moved bodies. Minimum screw-reserve gap **{facts['minimum_body_screw_gap_mm']:.6f}mm** and minimum plug/service-envelope gap **{facts['minimum_plug_service_gap_mm']:.6f}mm** stay positive. The two moved capacitors are separately enumerated in `review-facts.json`. This is conservative CAD-bound screening; physical screw/plug/motor/handling fit is not verified.

## Remaining star-via obstruction and explicit decision

Both original0.30mm holes and0.55mm lands remain unchanged. V_STAR_A's minimum drill-edge/SMT gap is **0.07506305mm**, and V_STAR_B's is **0.07493605mm**. Under the unchanged0.115mm radial budget their margins remain **−0.03993695 /−0.04006395mm**. Native nominal DRC does not establish these tolerance margins.

The driver-local EP/GND18 and EP/GND pad gaps are **0.4501261 /0.4498721mm**. A0.30mm hole plus two0.115mm budgets needs **0.530mm**. Translation/rotation of the complete driver or moving other components cannot change its internal gaps. Enlarging the board or moving JST/USB is not the obstruction identified here.

The strengthened necessary access test includes **wire-end-cap reach** as well as the whole0.275mm outer via radius, with another optimistic0.001mm reach allowance. It tests on-annulus endpoints, actual0.30mm wire radius, and even0.36mm stressed radius at128/256 curve subdivisions. Only the driver’s29 real top pads constrain it; every other component, other copper, layers and mechanical obstacles are omitted. The stressed0.72mm trace-centre region containing EP is closed by foreign-pad clearance buffers, and **all six access domains are empty at0.115mm**. A binary search gives an optimistic radial-budget ceiling about **0.0781mm** for this padstack/access class; the retained budget is roughly0.0369mm larger. Extra real obstacles cannot open this permissive domain. This rules out the studied fixed-land-pattern/original-hole escape class under rigid placement, not every imaginable land pattern or technology.

The remaining lock is the **supplier driver land pattern**, not component translation. Quantified counterfactuals, not adopted solutions:

| Required residual radial margin | Required local gap | Move GND18 inner edge outward | Move GND inner edge outward | Alternative symmetric EP x dimension |
| --- | --- | --- | --- | --- |
| 0 | 0.530mm | 0.079874mm | 0.080128mm | 3.039738mm |
| **+0.005mm** | **0.540mm** | **0.089874mm** | **0.090128mm** | **3.019738mm** |
| +0.010mm | 0.550mm | 0.099874mm | 0.100128mm | 2.999738mm |

For the+0.005mm example, shrinking the current3.1999936mm EP x dimension would require **0.180256mm total reduction**; alternatively translating the two GND lands outward requires the listed amounts and connected-copper requalification. These are dimensional requirements only: solder coverage, physical terminal contact, thermal/current behavior and the other copper gates would need qualification. The datasheet's3.15mm reference EP alone would yield only **0.475123 /0.474869mm gaps**, still below0.530mm. The reference land drawing is not tooling or supplier acceptance.

**Decision needed before attempting a star fix:** authorize and qualify a revised driver land pattern with the necessary extra gap and positive margin; original drills and every numerical gate stay required. The current task keeps the original drills and rules, so no smaller holes, EP cuts, pad translations, via-in-pad enablement, NC-pad removal or narrower return are adopted. The0.115mm budget still contains published0.075mm position plus existing assumed0.025mm radius growth and0.015mm registration; those assumptions are not verified supplier guarantees. No outreach is made.

## Entry point, rejection state and remaining gates

Pinned native CLI source generation exits0 in **{cli['CLI_command_exit']['wall_s']:.3f}s** with routing disabled and the documented schematic-drawing control; exact normal config restores. API and CLI physical copper, widths, net identity, source contract and poses match exactly. CLI's24 missing nonphysical endpoint annotations are enumerated; API annotation ownership is independently checked. All selected native geometry/thickness checks are zero. Native routing diagnostics retain300 port errors and4 style warnings; only the VREG length error is removed. Independent copper still has **59 open nets**.

The new native replay regression also rejects one-ULP fixed-CP edits, fake cached length, native-maximum changes, wrong VREG endpoint IDs and smaller holes. The preceding comparison regression and typecheck pass. The guard verifies the expected star rejection state; it does not make the manufacturing screen pass. CI retains the unchanged production locality gate25/59. Candidate locality remains43/59 with no lost pass.

**No next routing group runs:** the two star tolerance gates and16 candidate locality targets remain blocked. Completed routing/connectivity, actual VREG ground return, finished stack/drill/registration process, CAM, supplier assembly, physical fit/handling, thermal/current and hardware evidence remain absent. Draft only; no promotion, merge, order or outreach.
'''
report+='\n![NEMA14 JST VREG comparison](../artifacts/iteration-11/VREG-review.png)\n\nReproduce with the frozen install and geometry requirements, then run `python3 experiments/vreg-star/expand-artifacts.py`, `python3 experiments/vreg-star/test.py`, `python3 experiments/vreg-star/cli-verify.py` and `python3 experiments/vreg-star/compare-cli.py`. The guard validates the expected rejection state; it does not pass the remaining manufacturing gate.\n'
Path('docs/vreg-star-comparison.md').write_text(report)
# Review native pad/trace geometry, with no invented copper.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="760" viewBox="0 0 1160 760"><rect width="1160" height="760" fill="#f7f8fa"/>']
def text(x,y,s,n=16,c='#17212b'):svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{n}" fill="{c}">{html.escape(s)}</text>')
text(24,35,'NEMA14 JST · VREG capacitor placement and native escape',24);text(24,65,'Original 0.30 mm drills and all other 43 paths preserved. Two star margins remain rejected.',15)
for ox,data,title in [(24,resolve_copper_nets(b),'BEFORE · native wire 2.605856 mm'),(594,j,'CANDIDATE · native wire 0.990775 mm')]:
 svg.append(f'<rect x="{ox}" y="88" width="542" height="445" rx="8" fill="white" stroke="#cfd6df"/>');text(ox+14,117,title,18);clip=box(5.0,9.5,10.2,12.7);scale=96;svg.append(f'<g transform="translate({ox+18-5*scale},{144+12.7*scale}) scale({scale},{-scale})">')
 def poly(p,color):
  if p.is_empty:return
  if hasattr(p,'geoms'):
   for t in p.geoms:poly(t,color)
  else:svg.append('<path d="'+' '.join(('M' if i==0 else 'L')+f'{x},{y}' for i,(x,y) in enumerate(p.exterior.coords))+' Z" fill="'+color+'"/>')
 poly(box(9.8,9.8,16.2,16.2).intersection(clip),'#fff0ee');ss={e['source_trace_id']:e.get('name','') for e in data if e['type']=='source_trace'}
 for e in data:
  if e['type']=='pcb_smtpad' and e['layer']=='top':poly(g.pad_shape(e).intersection(clip),'#b7c0cb')
 for e in data:
  if e['type']!='pcb_trace' or ss[e['source_trace_id']]!='AUTHORED_VREG_BASELINE':continue
  for u,v in zip(e['route'],e['route'][1:]):
   line=LineString([(u['x'],u['y']),(v['x'],v['y'])]);poly(line.buffer(.096,quad_segs=128).intersection(clip),'#95d6ed');poly(line.buffer(.08,quad_segs=128).intersection(clip),'#176eb4')
 svg.append('</g>');text(ox+14,511,'Actual native copper: dark 0.16 mm; light +20% width; grey supplier pads.',11)
text(24,575,'VREG max_length stays 1 mm; true recomputed wire passes. Both endpoints are inside actual pads.',17);text(24,609,'Complete pad-centre path including pad access: 2.020794 mm. The full decoupling loop is not qualified.',16);text(24,643,f'VREG stressed foreign-pad minimum: {gaps[0]["stressed_copper_gap_mm"]:.6f} mm. Full nominal / stressed spacing: 0 failures.',16);text(24,683,'59 open nets; two original-hole star margins remain negative. No routing expansion or fabrication promotion.',16,'#a62b2b');text(24,725,'Measured footprint decision: +5 µm radial margin needs 0.540 mm gap, about 0.090 mm more than present.',16)
svg.append('</svg>');(r/'VREG-review.svg').write_text(''.join(svg))
