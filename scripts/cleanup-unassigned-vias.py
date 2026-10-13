import sys,json,pathlib
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'));import verify_supplier_connectivity as g
r=json.loads((root/'artifacts/jlcpcb-review/cam/audit.json').read_text());orphans=[island for issue in r['issues'] if issue['kind']=='unassigned-copper-islands' for island in issue['islands'] if not island['no_connect_pads']];removed=[]
def signature(key):
 es,rs=g.groups(key);groups={}
 for e,r in zip(es,rs):
  if e.get('pcb_port_id'):groups.setdefault(r,set()).add(e['pcb_port_id'])
 return sorted(sorted(v) for v in groups.values())
for island in orphans:
 a,b,c,d=island['bounds_mm'];x,y=(a+c)/2,(b+d)/2
 candidates=[v for v in g.j if v['type']=='pcb_via' and abs(v['x']-x)<1e-5 and abs(v['y']-y)<1e-5 and abs(v['outer_diameter']-(c-a))<1e-5 and abs(v['outer_diameter']-(d-b))<1e-5];assert len(candidates)==1, 'Only standalone actual-CAM orphan vias can be removed automatically'
 v=candidates[0];key=g.key(v);before=signature(key);g.j.remove(v);assert signature(key)==before, 'Removal changed terminal connectivity';removed.append(v)
g.path.write_text(json.dumps(g.j,indent=2)+'\n');(root/'artifacts/top-assembly/CAM-orphan-via-cleanup.json').write_text(json.dumps({'removed':removed,'all_live_terminal_connectivity_preserved':True,'identified_by_actual_Gerber_islands':True},indent=2)+'\n');print('Removed',len(removed),'actual-CAM orphan vias')
