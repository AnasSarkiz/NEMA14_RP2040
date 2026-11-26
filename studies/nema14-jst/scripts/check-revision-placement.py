"""Independent conservative courtyard/screw screen on the exact generated TSX.
This does not claim solid-body, plug-sweep, copper or manufacturing qualification.
"""
import argparse, hashlib, json, math
from pathlib import Path

def screen(board, contract):
    findings=[]
    sources={e['source_component_id']:e['name'] for e in board if e['type']=='source_component'}
    components={e['pcb_component_id']:e for e in board if e['type']=='pcb_component'}
    by_name={sources[c['source_component_id']]:c for c in components.values()}
    boards=[e for e in board if e['type']=='pcb_board']
    if len(boards)!=1 or any(boards[0].get(k)!=v for k,v in contract['board'].items()):findings.append({'kind':'board_contract'})
    for name,pose in contract['usb'].items():
        part=by_name.get(name,{})
        for key,expected in pose.items():
            actual=part.get(key)
            if key=='center':
                equal=actual and all(abs(actual[a]-expected[a])<1e-6 for a in ['x','y'])
            else:equal=actual==expected
            if not equal:findings.append({'kind':'usb_contract','part':name,'field':key,'actual':actual,'expected':expected})
    holes=[e for e in board if e['type']=='pcb_hole' and not e.get('pcb_component_id')]
    actual=sorted((round(e['x'],6),round(e['y'],6),round(e['hole_diameter'],6)) for e in holes)
    expected=sorted((h['x'],h['y'],h['hole_diameter']) for h in contract['holes'])
    if actual!=expected:findings.append({'kind':'mount_contract','actual':actual,'expected':expected})
    keepouts=[e for e in board if e['type']=='pcb_keepout']
    for hole in contract['holes']:
        matching=[e for e in keepouts if e.get('shape')=='circle' and all(abs(e.get('center',{}).get(a,999)-hole[a])<1e-6 for a in ['x','y'])]
        if len(matching)!=1 or matching[0].get('allow_placements') is not False or abs(matching[0].get('radius',0)-contract['screw_reserve_radius'])>1e-6 or set(matching[0].get('layers',[]))!={'top','inner1','inner2','bottom'}:
            findings.append({'kind':'screw_keepout_contract','mount':[hole['x'],hole['y']]})
    motor=by_name.get('J_MOTOR',{})
    if motor.get('insertion_direction')!='from_right':findings.append({'kind':'connector_direction','actual':motor.get('insertion_direction')})
    encoder=by_name.get('U_ENCODER',{})
    if encoder.get('layer')!='bottom' or any(abs(encoder.get('center',{}).get(a,999))>1e-6 for a in ['x','y']):findings.append({'kind':'encoder_axis'})
    checked=set()
    for item in board:
        if item['type']!='pcb_courtyard_outline' or item.get('layer')!='top':continue
        c=components[item['pcb_component_id']];name=sources[c['source_component_id']];checked.add(name)
        xs=[p['x'] for p in item['outline']];ys=[p['y'] for p in item['outline']]
        for h in contract['holes']:
            d=math.hypot(max(min(xs)-h['x'],0,h['x']-max(xs)),max(min(ys)-h['y'],0,h['y']-max(ys)))
            if d<contract['screw_reserve_radius']-1e-6:
                findings.append({'kind':'screw_reserve','part':name,'mount':[h['x'],h['y']],'courtyard_distance_mm':round(d,6),'intrusion_mm':round(contract['screw_reserve_radius']-d,6)})
    for name,c in by_name.items():
        if c['layer']=='top' and name not in checked:findings.append({'kind':'missing_courtyard','part':name})
    native=[{'type':e['type'],'message':e.get('message')} for e in board if e['type'].endswith('_error')]
    return {'screen_pass':not findings and not native,'checked_top_courtyards':len(checked),'native_errors':native,'findings':findings,'pcb_traces':sum(e['type']=='pcb_trace' for e in board),'pcb_vias':sum(e['type']=='pcb_via' for e in board),'mated_plug_and_sweep_verified':False,'power_and_kelvin_routing_verified':False,'manufacturing_qualified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('circuit_json');p.add_argument('--report');args=p.parse_args()
    path=Path(args.circuit_json);data=path.read_bytes();contract=json.loads(Path(__file__).with_name('mechanical-contract.json').read_text())
    report={'input':str(path),'input_sha256':hashlib.sha256(data).hexdigest(),**screen(json.loads(data),contract)}
    result=json.dumps(report,indent=2)+'\n'
    if args.report:Path(args.report).write_text(result)
    print(result,end='');return 0 if report['screen_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
