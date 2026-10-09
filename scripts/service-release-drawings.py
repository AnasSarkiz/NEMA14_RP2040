"""Generate bounded assembly, fabrication and supplier calibration review files."""
import pathlib,json,csv,math,hashlib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
from matplotlib.backends.backend_pdf import PdfPages
root=pathlib.Path(__file__).resolve().parents[1];j=json.loads((root/'artifacts/board.circuit.json').read_text());sc={e['source_component_id']:e for e in j if e['type']=='source_component'};pc={e['pcb_component_id']:e for e in j if e['type']=='pcb_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};ports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};cat=json.loads((root/'src/jlcpcb-catalog.json').read_text());name=json.loads((root/'package.json').read_text())['name'];out=root/'artifacts/assembly';out.mkdir(exist_ok=True)
sha=hashlib.sha256((root/'artifacts/board.circuit.json').read_bytes()).hexdigest();vias=[]
for v in j:
 if v['type']!='pcb_via':continue
 for p in j:
  if p['type']!='pcb_smtpad' or math.hypot(v['x']-p.get('x',1e9),v['y']-p.get('y',1e9))>.001:continue
  ref=sc[pc[p['pcb_component_id']]['source_component_id']]['name']
  if ref in ['U_MCU','U_PD','U_DRV']or v['pcb_via_id']=='service_filled_ground_cap_via':vias.append({'Via ID':v['pcb_via_id'],'Reference':ref,'X mm':v['x'],'Y mm':v['y'],'Finished drill mm':v['hole_diameter'],'Copper diameter mm':v['outer_diameter'],'Layers':'-'.join(v['layers']),'Required process':'IPC4761 TypeVII nonconductive resin filled; copper capped both faces; planar SMT land'})
with (out/'via_process.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(vias[0]));w.writeheader();w.writerows(vias)
notes=f'''# Fabrication requirements — {name}, service revision

Source SHA256 `{sha}`. Prototype fabrication/assembly acceptance remains pending.

- Board35x35x1.6mm, {next(e for e in j if e['type']=='pcb_board')['num_layers']}layers. ExternalCu>=35um, internalCu>=17.5um, plated barrels>=20um. Confirm actual stackup/copper and all process limits before manufacture.
- JST finished plated bores0.75+/-0.05mm, 2.00mm pitch; native hole size is deliberately overridden using official JST PH drawing. Other drills remain as exported. FourNPTHmounting holes3.2mm lowerpitch26,upper29.6mm; exactcenters in drawings/CAM. USBshellslotsPLATED milling. No untreated open SMT via-in-pad substitutions.
- Every via listed in `via_process.csv` requires **IPC4761 TypeVII**: nonconductive resin filled, copper capped both faces, final planar continuous solderable SMT land. Specify cap copper>=15um and finished surface step within+/-10um as procurement requirements; obtain supplier capability/X-section/planarity acceptance. Void/fill/cap quality and pad adhesion require supplier evidence and coupon/X-ray inspection. These are drawing requirements, not measured process values. RPincludes one additional filled/cappedC_USB GND via, drill0.25mm/pad0.50mm, explicitly included in CAM/table; confirm6.4:1 aspectratio process. All other ordinary vias are tented as represented; they must not intersect solder pads/paste.
- Topassemblyonly. Candidate stencil0.10mm with exposed-pad windows/60percentcoverage, reviewed narrowleadapertures. QFNvoiding/coplarity are assembler qualificationitems. Inspectallpin1/polarity orientations. Header is manualTHTafterreflow, noautomaticCPLplacement. USBshields hand-solderafterreflow. `manual_assembly.csv` recordsheaderprocess/tailtrim.
- Correct capacitor nominal7.7mm height;7.7+/-0.3 body +0.3 stand-off yields8.3mm maximum assemblyenvelope. Do not substitute the old5.82mm suppliermodel for clearance.
- Supplier pickupdatum/rotation must be calibrated againstnativepadcoordinates/assemblydrawings. `supplier-placement-calibration.csv` provides local datums and physicalpin1 references; it does not assertmachineconventions. Obtain actualsupplierplacementpreview and resolveeveryorientationbeforeassembly.
- Harness/temperature-certified insulation/frontcarrier assembly follow `docs/mechanical-fit.md`. Motorfrontthreads only; rearendcaps untouched. Physicalfit/thermal/electricalqualificationunperformed.
'''
(root/'docs/fabrication-requirements.md').write_text(notes);(out/'fabrication-notes.md').write_text(notes)
rows=[]
for cid,p in pc.items():
 s=sc[p['source_component_id']];ref=s['name']
 if ref not in cat['components']:continue
 pin1=next((q for q in ports.values()if q['pcb_component_id']==cid and sp[q['source_port_id']].get('pin_number')==1),None)
 rows.append({'Reference':ref,'MPN':s.get('manufacturer_part_number',''),'JLCPCB':cat['components'][ref],'Native CPL X mm':p['center']['x'],'Native CPL Y mm':p['center']['y'],'Native rotation deg':p.get('rotation',0),'Side':p.get('layer'),'Pin1 X mm':pin1['x']if pin1 else'','Pin1 Y mm':pin1['y']if pin1 else'','Process':'Manual THT'if ref=='J_MOTOR'else'Top SMT','Supplier pickup/rotation verification':'PENDING supplier preview; no assumed transform'})
with(out/'supplier-placement-calibration.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with PdfPages(out/'assembly-drawings.pdf')as pdf:
 fig,ax=plt.subplots(figsize=(8.27,11.69));ax.add_patch(Rectangle((-17.5,-17.5),35,35,fill=False,lw=2));ax.set_aspect('equal')
 for e in j:
  if e['type']=='pcb_hole':ax.add_patch(Circle((e['x'],e['y']),e['hole_diameter']/2,fill=False,color='red'))
  elif e['type']=='pcb_smtpad':
   if e.get('shape')=='polygon':ax.add_patch(Polygon([(p['x'],p['y'])for p in e['points']],facecolor='#dfbd58',edgecolor='#876500',lw=.15))
   else:
    w,h=e.get('width',e.get('radius',.1)*2),e.get('height',e.get('radius',.1)*2);ax.add_patch(Rectangle((e['x']-w/2,e['y']-h/2),w,h,angle=e.get('ccw_rotation',0),rotation_point='center',facecolor='#dfbd58',edgecolor='#876500',lw=.15))
  elif e['type']=='pcb_plated_hole':ax.add_patch(Circle((e['x'],e['y']),e.get('outer_diameter',.7)/2,facecolor='#dfbd58',edgecolor='#876500',lw=.3))
 for row in rows:
  ref=row['Reference'];x,y=row['Native CPL X mm'],row['Native CPL Y mm']
  if ref.startswith('U_')or ref in ['C_BULK','D_TVS','J_PD','J_DATA','J_MOTOR']:ax.text(x,y,ref,ha='center',va='center',fontsize=6,color='#173f8a',bbox=dict(facecolor='white',alpha=.75,pad=.2,edgecolor='none'))
  if row['Pin1 X mm']!='':ax.plot(row['Pin1 X mm'],row['Pin1 Y mm'],'mo',markersize=1.5)
 ax.annotate('PD15V / C-C',(-7,17.9),(-14,22),arrowprops=dict(arrowstyle='->'),fontsize=8);ax.annotate('USB DATA / A-C',(7,17.9),(3,22),arrowprops=dict(arrowstyle='->'),fontsize=8)
 ax.set_xlim(-22,22);ax.set_ylim(-22,25);ax.set_xlabel('X mm, board-center origin');ax.set_ylabel('Y mm');ax.set_title(name+'\nTopassembly / magenta dots: native physical pin1\nManual motorheader; verify supplier placement preview',fontsize=11)
 fig.text(.08,.1,'Motor: 1 BlackA+ / 2 GreenA- / 3 RedB+ / 4 BlueB-\nPCB NPTH lower26mm / upper29.6mm pitch; front motor26mm pattern is separate.\nCap+ and every diode/IC orientation must match native pads/netlist and supplierpreview.\nFilled/capped via list: via_process.csv. See fabrication-notes and mechanical-fit.\nSHA256 '+sha,fontsize=7);pdf.savefig(fig);fig.savefig(out/'assembly-top.svg');fig.savefig(out/'assembly-top.png',dpi=150);plt.close(fig)
 for page in range(math.ceil(len(rows)/34)):
  selected=rows[page*34:(page+1)*34];fig,ax=plt.subplots(figsize=(8.27,11.69));ax.axis('off');data=[[v['Reference'],v['MPN'],f"{v['Native CPL X mm']:.3f},{v['Native CPL Y mm']:.3f}",str(v['Native rotation deg']),v['JLCPCB']]for v in selected];table=ax.table(cellText=data,colLabels=['Ref','Exact MPN','Native center mm','Rotation','JLCPCB'],colWidths=[.11,.44,.2,.1,.15],loc='center');table.auto_set_font_size(False);table.set_fontsize(6.5);table.scale(1,1.5);ax.set_title(name+' - fitted placement reference\nNative source convention; supplier pickup/rotation approval pending',fontsize=10);pdf.savefig(fig);plt.close(fig)
(out/'assembly-review.json').write_text(json.dumps({'source_sha256':sha,'fitted_parts':len(rows),'filled_capped_vias':vias,'supplier_pickup_rotation_verified':False,'hardware_assembly_verified':False},indent=2)+'\n');print('Assemblydrawings',len(rows),'fittedparts;',len(vias),'specifiedVIPPOvias')
