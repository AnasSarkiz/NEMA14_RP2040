"""Full native placement and actual copper screen; courtyard overlap is independent of native DRC."""
from pathlib import Path
import json,sys,hashlib,importlib.util,math
from model import *
from routing_geometry import resolve_copper_nets
from shapely.ops import unary_union
path=Path(sys.argv[1]);j=resolve_copper_nets(json.loads(path.read_bytes()));ns=source_owner_names(j);ss={e['source_port_id']:e for e in j if e['type']=='source_port'};pports={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};pcs={ns[e['source_component_id']]:e for e in j if e['type']=='pcb_component' and ns[e['source_component_id']] in co};cn={e['pcb_component_id']:ns[e['source_component_id']] for e in j if e['type']=='pcb_component'};cs={cn[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in j if e['type']=='pcb_courtyard_outline' and e['layer']=='top' and cn[e['pcb_component_id']] in co};cc=court_conflicts(cs);cu=g.inspect(str(path));mechanical={}
for n in ['J_PD','J_DATA','J_MOTOR','U_ENCODER','C_ENCODER','C_ENCODER_BULK']:
 mechanical[n]=all(pcs[n][k]==co[n][k] for k in ['center','rotation','layer']);assert mechanical[n],n
screws=[];edges=[]
for n,p in cs.items():
 for x in [-13,13]:
  for y in [-13,13]:
   gap=p.distance(Point(x,y))-3.2
   if gap<-1e-6:screws.append({'part':n,'mount':[x,y],'intrusion_mm':-gap})
 if not __import__('shapely').geometry.box(-17.5,-17.5,17.5,17.5).buffer(1e-6).covers(p):edges.append(n)
# Fitted physical source ports keep the exact supplier pin-to-net contract, including INA240 and shunts.
def contract(data):
 nm=source_owner_names(data);return {(nm[e['source_component_id']],e['name']):e.get('subcircuit_connectivity_map_key') for e in data if e['type']=='source_port' and nm[e['source_component_id']] in co}
assert contract(j)==contract(b),'Source pin/net contract changed'
report={'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_pin_net_contract_unchanged':True,'fixed_mechanical_poses':mechanical,'top_courtyards':len(cs),'courtyard_conflicts':cc,'courtyard_screw_conflicts':screws,'courtyard_boundary_conflicts':edges,'independent':{k:len(cu[k]) for k in ['shorts','clearance_violations','drill_spacing_violations','hole_trace_violations','board_edge_violations','screw_keepout_violations','disconnected_nets']},'native_errors_by_type':{t:sum(e['type']==t for e in j) for t in sorted({e['type'] for e in j if e['type'].endswith('_error')})},'full_nominal_placement_pass':not cc and not screws and not edges and cu['geometric_clearance_pass'],'routed_controller':False,'manufacturing_qualified':False};out=Path(sys.argv[2]);out.write_text(json.dumps(report,indent=2)+'\n');out.with_suffix('.copper.json').write_text(json.dumps(cu,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['courtyard_conflicts','fixed_mechanical_poses']},indent=2));print('courtyard conflicts',len(cc))

raise SystemExit(0 if report["full_nominal_placement_pass"] else 1)
