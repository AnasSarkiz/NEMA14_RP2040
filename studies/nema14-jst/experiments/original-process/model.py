"""Read real native baseline geometry; all transforms stay outside the accepted source."""
from pathlib import Path
import json,gzip,math,sys,importlib.util
sys.path.insert(0,'scripts')
from native_sources import source_owner_names
from shapely.geometry import Point,Polygon,LineString,box
from shapely import affinity
s=importlib.util.spec_from_file_location('g','scripts/inspect-copper.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(p):
 p=Path(p);return json.loads(p.read_bytes() if p.exists() else gzip.decompress(Path(str(p)+'.gz').read_bytes()))
def index(j):
 names=source_owner_names(j);co={names[e['source_component_id']]:e for e in j if e['type']=='pcb_component' and e['source_component_id'] in {e['source_component_id'] for e in j if e['type']=='source_component'}};pc={e['pcb_component_id']:names[e['source_component_id']] for e in j if e['type']=='pcb_component'};sp={e['source_port_id']:e for e in j if e['type']=='source_port'};pp={e['pcb_port_id']:e for e in j if e['type']=='pcb_port'};ports={(names[sp[e['source_port_id']]['source_component_id']],sp[e['source_port_id']]['name']):e for e in j if e['type']=='pcb_port'};courts={pc[e['pcb_component_id']]:Polygon([(p['x'],p['y']) for p in e['outline']]) for e in j if e['type']=='pcb_courtyard_outline' and e['layer']=='top'};return names,co,pc,sp,pp,ports,courts
b=read('artifacts/iteration-9/final.circuit.json');names,co,pc,sp,pp,ports,courts=index(b)
def transform(poly,n,q):
 c=co[n];return affinity.translate(affinity.rotate(poly,q[2]-c['rotation'],origin=(c['center']['x'],c['center']['y'])),q[0]-c['center']['x'],q[1]-c['center']['y'])
def pin(n,p,q):
 a=ports[n,p];v=transform(Point(a['x'],a['y']),n,q);return [v.x,v.y]
