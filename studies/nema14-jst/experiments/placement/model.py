"""Read the exact public diagnostic and transform actual native geometry."""
from pathlib import Path
import json,gzip,math,sys,importlib.util
sys.path.insert(0,'scripts')
from shapely.geometry import Polygon,Point,LineString
from shapely import affinity
from native_sources import source_owner_names
s=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(p):
 p=Path(p);return json.loads(p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes()))
b=read('artifacts/iteration-6/current-board.circuit.json');names=source_owner_names(b);co={names[e['source_component_id']]:e for e in b if e['type']=='pcb_component' and e['source_component_id'] in {e['source_component_id'] for e in b if e['type']=='source_component'}};pc={e['pcb_component_id']:names[e['source_component_id']] for e in b if e['type']=='pcb_component'};sp={e['source_port_id']:e for e in b if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in b if e['type']=='pcb_port'};ports={(names[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in b if e['type']=='pcb_port'};courts={pc[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in b if e['type']=='pcb_courtyard_outline' and e['layer']=='top'}
poses={n:[c['center']['x'],c['center']['y'],c['rotation']] for n,c in co.items()}
def transform(shape,n,q):
 c=co[n];return affinity.translate(affinity.rotate(shape,q[2]-c['rotation'],origin=(c['center']['x'],c['center']['y'])),q[0]-c['center']['x'],q[1]-c['center']['y'])
def pin(n,p,q):
 a=ports[n,p];v=transform(Point(a['x'],a['y']),n,q);return [v.x,v.y]
def courtyard(n,q):return transform(courts[n],n,q)
def court_conflicts(parts):
 rows=[]
 for i,(n,p) in enumerate(parts.items()):
  for m,z in list(parts.items())[i+1:]:
   area=p.intersection(z).area
   if area>1e-8:rows.append({'a':n,'b':m,'overlap_mm2':area})
 return rows
