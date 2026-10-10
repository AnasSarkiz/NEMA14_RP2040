"""Remove only actual CAM islands positively proven to be unanchored ground fill.
No checker exclusions. Source pad, trace, via and drill records remain unchanged.
"""
import json,pathlib,hashlib,importlib.util
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=pathlib.Path(__file__).resolve().parents[1];path=root/'artifacts/board.circuit.json';original=path.read_bytes();j=json.loads(original);audit=json.loads((root/'artifacts/manufacturing/audit.json').read_text());assert audit['source_sha256']==hashlib.sha256(original).hexdigest()
spec=importlib.util.spec_from_file_location('cam',root/'scripts/audit-manufacturing.py');cam=importlib.util.module_from_spec(spec);spec.loader.exec_module(cam)
directory=root/'artifacts/manufacturing';cut=unary_union([cam.drill(p)[0]for p in directory.glob('*.drl')]);layers={'top':'F_Cu','bottom':'B_Cu','inner1':'In1_Cu','inner2':'In2_Cu'};actual={l:cam.gerber(directory/(name+'.gbr'))[0].difference(cut)for l,name in layers.items()if(directory/(name+'.gbr')).exists()}
k=next(e['subcircuit_connectivity_map_key']for e in j if e['type']=='source_net'and e['name']=='GND');coords=lambda r:[(p['x'],p['y'])for p in r['vertices']]
def pour(e):
 b=e['brep_shape'];return Polygon(coords(b['outer_ring']),[coords(r)for r in b.get('inner_rings',[])])
ground={l:unary_union([pour(e)for e in j if e['type']=='pcb_copper_pour'and e.get('subcircuit_connectivity_map_key')==k and e['layer']==l]).difference(cut)for l in actual};cuts={};rows=[]
for island in audit['connectivity']['unassigned_island_details']:
 if island['no_connect_pads']or island['area_mm2']<1e-5:continue
 assert len(island['layers'])==1,'Cross-layer unassigned islands require separate via investigation'
 l=island['layers'][0];gs=list(actual[l].geoms)if hasattr(actual[l],'geoms')else[actual[l]];matches=[q for q in gs if max(abs(a-b)for a,b in zip(q.bounds,island['bounds_mm']))<1e-5 and abs(q.area-island['area_mm2'])<1e-5];assert len(matches)==1,(island,len(matches));q=matches[0]
 assert q.area<10 and q.difference(ground[l].buffer(.0002)).area<1e-6,'Not a verified small ground-fill-only CAM island'
 overlaps=[]
 for e in j:
  t=e['type'];gs=[]
  if t in ['pcb_smtpad','pcb_plated_hole','pcb_via']and l in e.get('layers',[e.get('layer','top')]):gs=[cam.shape(e).difference(cut)]
  elif t=='pcb_trace':
   gs=[LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2,quad_segs=64).difference(cut)for a,b in zip(e['route'],e['route'][1:])if a['route_type']==b['route_type']=='wire'and a['layer']==b['layer']==l]
  if any(q.intersection(g).area>1e-7 for g in gs):overlaps.append(e.get(t+'_id'))
 assert not overlaps,('Not fill-only; inspect source copper anchors',island,overlaps)
 cuts.setdefault(l,[]).append(q.buffer(.01));rows.append({**island,'source_ground_fill_only_proven':True,'no_source_pad_trace_or_via_copper_contact':True,'actual_contour_cut_guard_mm':.01})
assert rows,'No verified fill-only islands to remove'
def ring(r):return {'vertices':[{'x':float(x),'y':float(y)}for x,y in list(r.coords)[:-1]]}
out=[];removed=0
for e in j:
 if e['type']!='pcb_copper_pour'or e.get('subcircuit_connectivity_map_key')!=k or e['layer']not in cuts:out.append(e);continue
 p=pour(e);q=p.difference(unary_union(cuts[e['layer']]));removed+=p.area-q.area
 for i,piece in enumerate(q.geoms if hasattr(q,'geoms')else[q]):
  if piece.is_empty:continue
  assert piece.geom_type=='Polygon';out.append({**e,'pcb_copper_pour_id':e['pcb_copper_pour_id']+f'_campruned_{i}','brep_shape':{'outer_ring':ring(piece.exterior),'inner_rings':[ring(r)for r in piece.interiors]}})
assert 0<removed<sum(r['area_mm2']for r in rows)+2,(removed,rows)
assert [e for e in out if e['type']!='pcb_copper_pour']==[e for e in j if e['type']!='pcb_copper_pour']
assert path.read_bytes()==original,'Source changed during frozen CAM island review'
path.write_text(json.dumps(out,indent=2)+'\n');(root/'artifacts/validation/actual-cam-ground-prune.json').write_text(json.dumps({'source_before_sha256':hashlib.sha256(original).hexdigest(),'boardSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'isolated_actual_CAM_copper':rows,'ground_only_removed_area_mm2':removed,'method':'Reparse actual RS274X/Excellon. Match each unassigned single-layer conductor by exact bounds/area, prove it lies wholly in source GND fill after drills and contacts no source pad/trace/via Cu. Subtract its actual contour plus0.01mm guard from GND pours only. All pad/trace/via/drill records remain byte-equivalent. Re-export and rerun native and actual CAM checks; no audit errors are excluded.'},indent=2)+'\n');print('Removed verified fill-only CAM islands',len(rows),'area',removed)
