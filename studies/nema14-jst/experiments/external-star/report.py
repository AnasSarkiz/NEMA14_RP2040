"""Measured rejection report and original geometry review; manufacturer PDFs are linked, not republished."""
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
import html,hashlib
r=Path('artifacts/iteration-12');series=read(r/'external-audit.json');direct=read(r/'direct-audit.json');ref=read(r/'manufacturer-comparison.json');cli=read(r/'cli-replay.json');branches=read(r/'local-branches.json');facts={}
for mode,audit in [('external',series),('direct',direct)]:
 j=read(r/(mode+'.circuit.json'));native=read(r/(mode+'-native.json.all-routing.json'));src={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'};tr={e['pcb_trace_id']:e for e in j if e['type']=='pcb_trace'};process=read(r/(mode+'-process.json'));facts[mode]={'input_sha256':hashlib.sha256((r/(mode+'.circuit.json')).read_bytes()).hexdigest(),'trace_count':sum(e['type']=='pcb_trace' for e in j),'via_count':22,'native_connectivity_errors':native['by_type'],'native_endpoint_findings':[{**e,'actual_path':src[tr[e['pcb_trace_id']]['source_trace_id']]} for e in native['findings'] if e['type']=='pcb_trace_error'],'process_summary':process['summary'],'stage_allowed':False,'stage_blockers':['Compulsory intermediate ground-land width at most0.280010mm, below retained0.60mm','Two native dangling inner-pad endpoints retained','Full VREG ground loop, VBB bypass return and VCP reservoir wiring open','Full-board59 disconnected nets and pre-existing locality gates'],'physical_locks_and_supplier_footprint_exact':True,'promoted':False}
(r/'decision.json').write_text(json.dumps({'baseline_head':'731ff153d4c5968dd137cbcc84fbc4367cfeb654','controls':facts,'recommendation':'Stop routing/placement sweeps. Review an intentional under-EP thermal-via fabrication and assembly process on a source-reviewed land pattern, with explicit own-pad policy approval and all foreign clearances retained. No such policy or footprint change adopted.','manufacturer_reference_is_not_a_solution_to_original_between-pad_0_30_holes':True,'no_merge_order_or_outreach':True},indent=2)+'\n')
report=f'''# NEMA14 JST external-star decision

**Stop the placement/routing sweep.** Two bounded external controls can connect the sense-resistor grounds to EP and clear the original drill screen, but both require an intermediate **0.280010mm ground land**, so they do not retain the required0.60mm planar return. The complete manufacturer reference pattern does not solve the between-pad drill windows. A qualified design/fabrication decision is needed; no production footprint or gate changed.

The separate controls inherit731ff15 and preserve the35mm outline, screw/case envelope, selected side-facing JST, both USB poses, bottom encoder, top DNP caps, component poses, supplier pads and sensing pin/net contract. Four GND vias move; every hole remains0.30mm and every land0.55mm. The other18 via whole records and38 non-return path arrays remain exact, including the four Kelvin pickups, CP, VREG positive leg and buzzer. Prior candidates, main and original boards are untouched.

## Fitted driver and manufacturer reference

The design BOM/native source specifies **A4988SETTR-T, catalogue C38437**, the ET28-contact QFN plus EP. The official [A4988 Rev8 datasheet](https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.pdf), pages12/18/19, calls for soldered PAD ground, external GND3/18 ties and thermal vias; its land drawing is a reference, not tooling approval. Nominal adjacent-pad spacing is at least0.20mm. The drawing was visually inspected; the isolated native dimensional fixture reproduces its dimensions without replacing the production import.

| Dimension | Imported current land pattern | Published complete reference |
| --- | --- | --- |
| EP | 3.1999936mm square | 3.15mm square |
| Peripheral land | 0.8999982×0.2800096mm pill | 1.15×0.30mm rectangle |
| Opposite-row centre separation | 4.999990mm | 4.80mm |
| Pitch | 0.500380mm | 0.50mm |
| Minimum adjacent-pad gap | 0.220370mm | 0.200000mm |
| EP/GND18 and EP/GND windows | 0.450126/0.449872mm | **0.250000mm each** |

The current pattern differs from the reference; its nominal pad spacing passes the cited minimum. This comparison is not a terminal-coverage, stencil or assembly approval. A3.15mm EP substituted alone into the imported pattern is **not the complete reference pattern**. The earlier3.019738mm EP proposal was an unsupported dimensional counterfactual, not a published land alternative.

[Allegro AN26009 Rev14](https://www.allegromicro.com/-/media/files/application-notes/an26009-soldering-methods-for-allegro-products.pdf) discusses filling vias to reduce solder loss/voiding and hidden QFN joint inspection. Its general voiding examples do not qualify this board. An exact fitted-device alternative land, stencil/fill process and board-specific thermal acceptance were not found in the examined sources. The generic wettable-flank guide was excluded because applicability to this exact ET part was not verified. Retrieved PDF hashes and page references are preserved in `manufacturer-comparison.json`; manufacturer PDFs/images are not republished.

## Two bounded external controls

The first control moves V_GA→(3.700,7.350), V_STAR_A→(4.300,7.449873), V_GB→(11.800,6.360), V_STAR_B→(10.830,6.949493). It routes two0.60mm branches through inner1, then joins EP through the actual GND18/GND lands. The second control removes those layer detours and uses top copper to the same external via locations. No autorouter runs.

| Check | Two-barrel control | Top-direct control |
| --- | --- | --- |
| Native traces / real vias | 46 /22 | 44 /22 |
| Nominal shorts / spacing findings | **0 /0** | **0 /0** |
| +20% width-stress shorts / spacing | **0 /0** | **0 /0** |
| Adjusted SMT / annular / inner-via failures | **0 /0 /0** | **0 /0 /0** |
| Combined +20% width/drill failures | **0**, minimum+0.009249mm | same |
| Minimum adjusted SMT / annular margin | **+0.008730 /+0.010000mm** | same |
| Required intermediate ground-pad width upper bound | **0.280010mm** | **0.280010mm** |
| Full-board disconnected nets | **59** | **59** |
| Native port errors / endpoint errors / style warnings | **298 /2 /4** | **298 /2 /4** |

Clean native spacing checks and0.60mm trace properties do not prove a0.60mm physical return. Removing the actual intermediate ground pad disconnects each isolated phase. The copper cross-section through the middle of that indispensable pad is only0.2800096mm, a53.33% reduction from the target; contact lenses may constrain it further. This intermediate neck is not a source/target pad or a qualified vertical barrel. No new pad exception is assumed.

Current flow is checked after subtracting **all real via holes**. A's authored series path is **5.092772mm**, including1.480000mm ground-pad access and0.283000mm of conducted barrel travel; both barrels are required, and it exceeds5mm. B's apparent5.577702mm serial route is **bypassed by actual top copper**; neither barrel is required, so it is not reported as B's true current path.

The top-direct control deliberately removes that ambiguity. Explicit hole-avoiding paths along real annuli are **4.682739 /4.501442mm**, with zero conducted vertical barrels and pad access included. They are conductive paths inside the measured copper, **not0.60mm-wide qualifying returns**. Thus improving length does not remove the indispensable narrow pad. Neither control is promoted.

The full native checker retains two dangling-start errors at RETURN_A_EP(5.840,7.449873) and RETURN_B_EP(9.360,6.949493). Independent geometry confirms end-cap/pad overlap, but no check or endpoint error is suppressed. The exact objects and source owners are in `decision.json`. The top-direct control additionally loses six unused via-port net annotations in native source metadata; fitted part pins and explicit physical via GND nets remain unchanged, with every delta enumerated.

## Independent loop, sensing and mechanical checks

- All four real inline-shunt pad cuts still pass, with zero shared winding/Kelvin copper outside the pickup pads. Both prospective low-side paths reach EP and externally tie GND3/18, without substituting internal chip connections. The ceramic/bulk supply-return grounds remain on separate islands from EP, so a completed motor-current return loop is not claimed.
- The VREG positive leg remains0.990775mm, but **C_VREG.pin2 is a separate ground island**. No complete VREG decoupling copper loop exists; its length and area are recorded as **null**, not fabricated estimates. Ground-pad-to-EP edge separation alone is1.850131mm. The short positive-leg native pass does not qualify decoupling.
- Both CP legs retain drilled-copper continuity and stressed clearance to true EP, native square keepout and actual screw circle. The VCP reservoir-to-driver and reservoir-to-VBB connections remain open; the complete charge-pump supply system is not qualified.
- Buzzer branch continuity is independently rechecked, including rejection when either supply barrel is removed. External flyback wire travel is **13.324631mm**; external switch wire plus conducted barrels is **35.399209mm**. These are unchanged branch sums, excluding internal device/winding paths.
- Every fitted component pose/CAD placement and supplier pad is unchanged. Both native and independent copper checks retain all four screw exclusions and board edge clearances. Prior supplier-body fit bounds therefore remain applicable; no physical assembly/handling test is claimed. The moved V_GB has a new conservative bounding projection under R_SB, requiring explicit fill/mask/planarity and assembly review; this is not a measured solid collision. There are no copper pours or via drill centres inside EP in these diagnostic outputs, so board-specific thermal performance remains unqualified.

## Source-supported alternatives and decision

The complete published reference's0.25mm windows cannot fit a0.30mm hole even before the retained0.115mm radial budget. Its0.30mm peripheral lands also do not provide a continuous0.60mm external return neck. It is a source-backed land-pattern reference, **not a drop-in solution** to these constraints.

The source-backed direction to qualify is **intentional thermal vias at EP**, with a reviewed land/stencil and solder-voiding process. It requires an explicit design/fabrication decision about intentional own-ground via-in-pad handling. The current all-SMT hole rule and native prohibition would still reject it; neither is reinterpreted or changed here. Foreign-net clearances,0.30mm drills, return width and total budget remain requirements. Specific via fill/cap/planarity, actual drill/registration tolerances, solder contact/voiding, stencil/reflow, electrical/X-ray inspection, CAM and board thermal/current performance need qualification before adoption. No supplier is contacted.

**Recommendation:** freeze further placement/routing experiments and decide whether to qualify that intentional EP-via process. Do not force an unsupported EP trim or accept a narrow ground-pin bridge. If every present gate remains fixed, these studied alternatives remain rejected.

## Native entry point and evidence

Native CLI source generation passes for both separate TSX entries in **{cli['exit']['runs'][0]['wall_s']:.3f}s /{cli['exit']['runs'][1]['wall_s']:.3f}s**, with routing disabled and the documented temporary schematic-drawing control; normal configuration restores exactly. CLI/API physical/source geometry matches, with32/28 missing nonphysical CLI terminal annotations explicitly listed. All selected geometry/thickness checks pass; the full native endpoint/connectivity errors above remain.

Fresh native replay, rejection controls and typecheck pass locally. Controls reject driver-EP edits, real pin-net changes, CP copper edits, return-width changes, false VREG length cache, native length-limit changes and board-clearance changes. The isolated reference fixture is freshly replayed. The preceding VREG comparison regression also passes. The guard verifies the rejection state; it does not clear fabrication gates. Production/locality source is unchanged.

No further bounded routing runs because physical width, native endpoint, full-loop and locality gates fail. Main, original boards, prior candidates and the accepted source remain untouched; draft only, no merge/order/outreach.
'''
report+='\n![NEMA14 JST external return and reference comparison](../artifacts/iteration-12/external-review.png)\n\nReproduce after the frozen install and geometry requirements with `python3 experiments/external-star/expand-artifacts.py`, `python3 experiments/external-star/test.py`, `python3 experiments/external-star/cli-verify.py` and `python3 experiments/external-star/compare-cli.py`. The guard validates known rejections; it is not a fabrication pass. Manufacturer source URLs/hashes are archived; PDFs remain external references.\n'
Path('docs/external-star-decision.md').write_text(report)
# Original schematic geometry figures, not a copy of the manufacturer's drawing.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="990" viewBox="0 0 1160 990"><rect width="1160" height="990" fill="#f7f8fa"/>']
def text(x,y,s,n=16,c='#17212b'):svg.append(f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="{n}" fill="{c}">{html.escape(s)}</text>')
def poly(p,color):
 if p.is_empty:return
 if hasattr(p,'geoms'):
  for q in p.geoms:poly(q,color)
 else:svg.append('<path d="'+' '.join(('M' if i==0 else 'L')+f'{x},{y}' for i,(x,y) in enumerate(p.exterior.coords))+' Z" fill="'+color+'"/>')
text(24,36,'NEMA14 JST · external return and land-pattern decision',24);text(24,66,'Clean spacing and drill screens still leave a compulsory 0.280010 mm copper neck; required return is 0.60 mm.',15)
j=resolve_copper_nets(read(r/'direct.circuit.json'));nm,cs,pc,ss,pp,ps,ct=index(j);st={e['source_trace_id']:e.get('name','') for e in j if e['type']=='source_trace'}
for ox,phase,pin,clip in [(24,'A','GND18',box(3.15,6.6,6.5,8.4)),(594,'B','GND',box(9.0,6.0,12.35,7.8))]:
 svg.append(f'<rect x="{ox}" y="88" width="542" height="340" rx="8" fill="white" stroke="#cfd6df"/>');text(ox+14,117,'TOP CONTROL '+phase+' · pad bridge fails width',18);scale=130;svg.append(f'<g transform="translate({ox+24-clip.bounds[0]*scale},{142+clip.bounds[3]*scale}) scale({scale},{-scale})">')
 for e in j:
  if e['type']=='pcb_smtpad' and e['layer']=='top':poly(g.pad_shape(e).intersection(clip),'#adc1d0' if e['pcb_port_id']==ps['U_DRV','EP']['pcb_port_id'] else '#b6bec9')
 for e in j:
  if e['type']=='pcb_trace' and st[e['source_trace_id']].startswith('RETURN_'+phase+'_'):
   for a,z in zip(e['route'],e['route'][1:]):
    line=LineString([(a['x'],a['y']),(z['x'],z['y'])]);poly(line.buffer(.36,quad_segs=128).intersection(clip),'#b8dfef');poly(line.buffer(.30,quad_segs=128).intersection(clip),'#2e86b8')
 land=next(e for e in j if e['type']=='pcb_smtpad' and e['pcb_port_id']==ps['U_DRV',pin]['pcb_port_id']);poly(g.pad_shape(land).intersection(clip),'#e3a53d');poly(LineString([(land['x'],land['y']-.1400048),(land['x'],land['y']+.1400048)]).buffer(.010).intersection(clip),'#bd2c30')
 for e in j:
  if e['type']=='pcb_via':poly(g.pad_shape(e,True).intersection(clip),'white')
 svg.append('</g>');text(ox+14,410,'Orange: actual compulsory pin land. White: actual 0.30 mm drill holes.',11)
text(24,463,'Hole-avoiding paths A 4.682739 / B 4.501442 mm fit 5 mm, but their pin bridges are not 0.60 mm wide.',16)
# Native local coordinates for the existing and transcribed reference patterns.
refj=read(r/'reference.circuit.json')
for ox,data,label,offset,rot in [(24,b,'IMPORTED · EP 3.199994; pill 0.900 × 0.280',co['U_DRV']['center'],co['U_DRV']['rotation']),(594,refj,'PUBLISHED REFERENCE · EP 3.150; rect 1.150 × 0.300',{'x':0,'y':0},0)]:
 svg.append(f'<rect x="{ox}" y="492" width="542" height="326" rx="8" fill="white" stroke="#cfd6df"/>');text(ox+14,521,label,15);svg.append(f'<g transform="translate({ox+275},663) scale(40,-40)">')
 for e in data:
  if e['type']!='pcb_smtpad' or data is b and e['pcb_component_id']!=co['U_DRV']['pcb_component_id']:continue
  p=affinity.translate(affinity.rotate(g.pad_shape(e),-rot,origin=(offset['x'],offset['y'])),-offset['x'],-offset['y']);poly(p,'#9ab9ce' if e.get('port_hints')==['pin29'] else '#b6bec9')
 svg.append('</g>');text(ox+14,799,'Dimensional transcription only; no supplier footprint change adopted.',11)
text(24,853,'Published reference windows are 0.250 mm, below even the original 0.300 mm drill diameter.',16)
text(24,887,'VREG capacitor ground is still a separate island. Full loop length / area are unknown; 59 nets remain open.',16,'#a62b2b')
text(24,923,'Decision: qualify intentional thermal vias at EP and the assembly process; all present gates stay unchanged.',16)
text(24,960,'Rejected controls only. No routing expansion, production footprint edit, merge, supplier contact or order.',15)
svg.append('</svg>');(r/'external-review.svg').write_text(''.join(svg))
