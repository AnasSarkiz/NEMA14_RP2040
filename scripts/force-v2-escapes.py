"""Open local via escapes, rerouting only copper that obstructs the new escape.

Supplier pads, drilled holes, thermal vias and accepted escape paths stay fixed.
Every displaced net remains an explicit open until the bulk router repairs it.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from shapely.geometry import Point, LineString
import verify_supplier_connectivity as g
from v2_copper_cleanup import prune_floating

ROOT=g.ROOT
print('FLOATING_COPPER_REMOVED',len(prune_floating(g)),flush=True)
only_port=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--only-port=')),None)
only_net=(g.sp[g.ports[only_port]['source_port_id']].get('subcircuit_connectivity_map_key')
          if only_port else None)
via_pad=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--via-pad-mm=')),.5))
assert .45<=via_pad<=.5
unlock_ports={q.split('=',1)[1] for q in sys.argv if q.startswith('--unlock-escape-port=')}
unlock_traces={e['pcb_trace_id'] for e in g.j if e['type']=='pcb_trace'
               and e['pcb_trace_id'].startswith('v2_escape_')
               and unlock_ports.intersection(e.get('pcb_port_ids',[]))}
unlock_ids=unlock_traces | {e['pcb_via_id'] for e in g.j if e['type']=='pcb_via'
                         and any(e['pcb_via_id'].startswith(t+'_via_') for t in unlock_traces)}
unlock_ids.update(q.split('=',1)[1] for q in sys.argv if q.startswith('--unlock-escape-id='))
def protected(e):
    uid=e.get(e['type']+'_id','')
    return uid not in unlock_ids and uid.startswith(('v2_escape_','v2_thermal_','oscillator_v2_','usb_v2_'))
def pieces(e):
    if e['type']=='pcb_via':return [(l,Point(e['x'],e['y']).buffer(e['outer_diameter']/2)) for l in e['layers']]
    return [(a['layer'],LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2))
            for a,b in zip(e['route'],e['route'][1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']]

report_path=Path(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--escape-log=')),
                      ROOT/'artifacts/v2/routing/forced-escapes.json'))
history=json.loads(report_path.read_text()) if report_path.exists() else []
failed=set()
with tempfile.TemporaryDirectory(prefix='nema14-v2-local-') as temporary:
    directory=Path(temporary)
    for attempt in range(100):
        request=None
        for net,name in g.nets.items():
            if only_net is not None and net!=only_net:continue
            if '--ground' in sys.argv and name!='GND':continue
            if name in ['XIN','XOUT','XTAL_OUT']:continue
            if name=='GND' and '--ground' not in sys.argv:continue
            elements,roots=g.groups(net);islands={}
            for e,r in zip(elements,roots):
                if e.get('pcb_port_id'):islands.setdefault(r,[]).append(e)
            if len(islands)<2:continue
            through={r for e,r in zip(elements,roots) if e['type'] in ['pcb_via','pcb_plated_hole']}
            for root,pads in islands.items():
                if root in through:continue
                pad=next((p for p in pads if p['pcb_port_id'] not in failed
                          and (only_port is None or p['pcb_port_id']==only_port)),None)
                if pad is not None:request=(net,name,pad);break
            if request:break
        if request is None:break
        net,name,pad=request;port=pad['pcb_port_id'];label=g.src[g.comp[pad['pcb_component_id']]['source_component_id']]+'.'+g.sp[g.ports[port]['source_port_id']]['name']
        added=None;removed=None
        for step,margin in [(.025,.015),(.0125,.016),(.0125,.005),(.0125,.003)]:
            retained=[e for e in g.j if e['type'] not in ['pcb_trace','pcb_via','pcb_copper_pour'] or protected(e) or (e['type']=='pcb_via' and g.key(e)==net)]
            probe=directory/'probe.circuit.json';probe.write_text(json.dumps(retained,indent=2)+'\n')
            log=directory/'probe.log'
            command=[sys.executable,str(ROOT/'scripts/route-v2-repair.py'),'--source',str(probe),'--escape-islands','--escape-port='+port,'--net='+name,'--protect-signals','--via-pad-mm='+str(via_pad),'--grid-step-mm='+str(step),'--grid-margin-mm='+str(margin),'--repair-log='+str(directory/'repairs.json'),'--keep-floating-copper']
            command.extend(q for q in sys.argv if q.startswith('--escape-via-'))
            if name=='GND':command.append('--ground')
            with log.open('w') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,cwd=ROOT)
            if result.returncode:raise RuntimeError(log.read_text())
            old_ids={e.get(e['type']+'_id') for e in retained if e['type'] in ['pcb_trace','pcb_via']}
            candidate=[e for e in json.loads(probe.read_text()) if e['type'] in ['pcb_trace','pcb_via'] and e[e['type']+'_id'] not in old_ids]
            if not candidate:
                details=[line for line in log.read_text().splitlines() if 'TRAPPED_ESCAPE' in line or 'UNROUTED' in line]
                print('ESCAPE_GRID_BLOCKED',port,step,margin,details[-1:] or ['no construction candidate'],flush=True)
                continue
            new_geometry=[(l,s) for e in candidate for l,s in pieces(e)]
            invalid=False;reason=None
            for e in g.j:
                if e['type'] in ['pcb_smtpad','pcb_plated_hole']:
                    shape=g.geometry(e)
                    for new in candidate:
                        if new['type']=='pcb_via' and shape.intersection(Point(new['x'],new['y']).buffer(new['outer_diameter']/2)).area>1e-8:
                            invalid=True;reason=reason or ('via overlaps supplier pad '+str(e.get('pcb_port_id')))
                    if g.key(e)==net:continue
                    if any(l in e.get('layers',[e.get('layer','top')]) and s.distance(shape)<.15-1e-6 for l,s in new_geometry):
                        invalid=True;reason=reason or ('foreign supplier-pad clearance '+str(e.get('pcb_port_id')))
            if invalid:
                print('ESCAPE_REJECTED',port,step,margin,reason,flush=True);continue
            rip=set()
            for e in g.j:
                if e['type'] not in ['pcb_trace','pcb_via'] or g.key(e)==net:continue
                if any(l==other_l and s.distance(other)<.15-1e-6 for l,s in new_geometry for other_l,other in pieces(e)):
                    if protected(e):invalid=True;reason='protected copper '+e[e['type']+'_id'];break
                    rip.add(e[e['type']+'_id'])
            if invalid:
                print('ESCAPE_REJECTED',port,step,margin,reason,flush=True);continue
            # A removed barrel cannot remain implicitly referenced by a route.
            dead_vias=[e for e in g.j if e['type']=='pcb_via' and e['pcb_via_id'] in rip]
            for e in g.j:
                if e['type']!='pcb_trace':continue
                if any(any(abs(q['x']-v['x'])<1e-6 and abs(q['y']-v['y'])<1e-6 for q in e['route']) for v in dead_vias):
                    if protected(e):invalid=True;break
                    rip.add(e['pcb_trace_id'])
            if invalid:continue
            added,removed=candidate,rip;break
        if added is None:
            failed.add(port);print('NO_LOCAL_ESCAPE',name,label,flush=True);continue
        g.j[:]=[e for e in g.j if e.get(e['type']+'_id') not in removed]
        g.j.extend(added)
        row={'net':name,'terminal':label,'pcb_port_id':port,'added':[e[e['type']+'_id'] for e in added],'removed':sorted(removed)}
        history.append(row);print('LOCAL_ESCAPE',json.dumps(row),flush=True)
        g.path.write_text(json.dumps(g.j,indent=2)+'\n')
        report_path.write_text(json.dumps(history,indent=2)+'\n')
        if only_port:break
g.path.write_text(json.dumps(g.j,indent=2)+'\n')
print(json.dumps({'local_escapes_total':len(history),'unescaped_ports':sorted(failed),'source_sha256':hashlib.sha256(g.path.read_bytes()).hexdigest()}))
