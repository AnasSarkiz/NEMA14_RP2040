"""Finish physically disconnected nets on exact supplier geometry.

The conservative routing grid is only a construction aid. Native DRC and the
independent physical/CAM checks are required afterward.
"""
import json, math, heapq, sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
from shapely.ops import unary_union
from v2_route_io import g
from v2_copper_cleanup import prune_floating

if '--keep-floating-copper' not in sys.argv:
    print('FLOATING_COPPER_REMOVED',len(prune_floating(g)),flush=True)

j=g.j;ROOT=g.ROOT
STEP=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--grid-step-mm=')),.025))
assert STEP in [.025,.0125]
LOW=-17.5;N=round(35/STEP)+1
repair_log=Path(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--repair-log=')),ROOT/'artifacts/v2/routing/grid-repairs.json'))
construction_margin=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--grid-margin-mm=')),.02));assert .003<=construction_margin<=.02
layers=['top','bottom'] if next(e for e in j if e['type']=='pcb_board')['num_layers']==2 else ['top','inner1','inner2','bottom']
nets={e['subcircuit_connectivity_map_key']:e for e in j if e['type']=='source_net'}
traces={e['subcircuit_connectivity_map_key']:e['source_trace_id'] for e in j if e['type']=='source_trace'}
for k,name in g.nets.items():
 if k not in nets:nets[k]={'name':name,'source_net_id':None}
xy=lambda x,y:(round((x-LOW)/STEP),round((y-LOW)/STEP))
world=lambda q:(LOW+q[0]*STEP,LOW+q[1]*STEP)
SOFT_ELIGIBLE=set()
soft_crossing_cost=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--rip-cost=')),30));assert 1<=soft_crossing_cost<=30
soft_wire=None
goal_pad_number=next((int(q.split('=',1)[1]) for q in sys.argv if q.startswith('--goal-pad=')),None)
start_pad_number=next((int(q.split('=',1)[1]) for q in sys.argv if q.startswith('--start-pad=')),None)
avoid_refs={q.split('=',1)[1] for q in sys.argv if q.startswith('--avoid-ref=')}
kelvin='--kelvin' in sys.argv
escape_islands='--escape-islands' in sys.argv
escape_port=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--escape-port=')),None)
kelvin_target=None
kelvin_start_ids=set()
def pad_reference(p):
    return g.src[g.comp[p['pcb_component_id']]['source_component_id']]
def pad_number(p):
    return g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['pin_number']
def soft_eligible(e):
    name=g.nets.get(g.key(e),'')
    uid=e.get('pcb_trace_id',e.get('pcb_via_id',''))
    if uid.startswith(('v2_escape_','oscillator_v2_','v2_thermal_','usb_v2_')):return False
    if e['type']=='pcb_via' and ('--rip-ordinary-vias' not in sys.argv or name in {'GND','PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','VREG','VREF','VCP','BUCK_SW','BUCK_BST','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'}):return False
    if name in {'USB_DP','USB_DM','MCU_DP','MCU_DM','XIN','XOUT','XTAL_OUT','QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','QSPI_SS','RUN','SWCLK','SWDIO'} and not ('--rip-debug-branches' in sys.argv and name in {'RUN','SWCLK','SWDIO'}):return False
    protected_nets={q.split('=',1)[1] for q in sys.argv if q.startswith('--protect-net=')}
    if name in protected_nets:return False
    if '--rip-debug-branches' in sys.argv and name in {'RUN','SWCLK','SWDIO'}:return True
    if name in {q.split('=',1)[1] for q in sys.argv if q.startswith('--rip-net=')}:return True
    if '--rip-pd-branches' in sys.argv and name=='PD_VBUS' and not uid.startswith(('usb_','reviewed_local_')):return True
    if '--rip-power-branches' in sys.argv and name in {'V3V3','DATA_VBUS','LOGIC_IN'}:
        if not uid.startswith(('usb_','oscillator_','review_escape_','reviewed_local_')):return True
    if '--rip-ground-branches' in sys.argv and name=='GND' and not uid.startswith(('usb_','oscillator_','reviewed_local_','feedback_ground_escape_')):return True
    if '--protect-signals' in sys.argv:return False
    return name not in {'GND','PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','VREG','VREF','VCP','BUCK_SW','BUCK_BST','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'} and not uid.startswith(('usb_','review_escape_','reviewed_local_'))
def width_for_layer(layer):
    if '--adaptive-power-layers' in sys.argv:
        name=nets[net]['name']
        if name=='PD_VBUS':return .55 if layer.startswith('inner') else .3
        if name=='DATA_VBUS':return .3 if layer.startswith('inner') else .2
    return current_width

def blocked(net,via=False):
    global soft_wire
    soft_images=[Image.new('L',(N,N)) for _ in layers];soft_ds=[ImageDraw.Draw(im) for im in soft_images]
    draw_layers=['top','inner1','inner2','bottom'] if via and next(e for e in j if e['type']=='pcb_board')['num_layers']==4 else layers
    images=[Image.new('L',(N,N)) for _ in draw_layers];ds=[ImageDraw.Draw(im) for im in images]
    margin=max(.15+current_via_diameter/2+construction_margin,.20+current_via_hole/2+construction_margin) if via else .15+current_width/2+construction_margin
    def add(ls,geom,extra=0,soft=False):
        for l in ls:
            if l not in draw_layers:continue
            layer_margin=margin if via else .15+width_for_layer(l)/2+construction_margin
            p=geom.buffer(layer_margin+extra,quad_segs=16)
            pieces=list(p.geoms) if hasattr(p,'geoms') else [p]
            d=(soft_ds if soft else ds)[draw_layers.index(l)]
            for piece in pieces:
                if piece.geom_type=='Polygon' and not piece.is_empty:d.polygon([xy(x,y) for x,y in piece.exterior.coords],fill=1)
    for e in j:
        typ=e['type']
        if typ in ['pcb_smtpad','pcb_plated_hole']:
            if g.key(e)==net and not via and pad_reference(e) not in avoid_refs:continue
            # The motor terminal has a 0.40 mm annulus. Its actual 0.15 mm
            # foreign-copper setback already exceeds the plated-drill rule;
            # an additional blanket 0.10 mm construction pad is unnecessary.
            wide_annulus=(typ=='pcb_plated_hole' and e.get('shape')=='circle' and
                          (e['outer_diameter']-e['hole_diameter'])/2>=.4-1e-5)
            extra=-.15 if g.key(e)==net and via else .1 if typ=='pcb_plated_hole' and not wide_annulus else 0
            add(e.get('layers',[e.get('layer','top')]),g.geometry(e),extra)
        elif typ=='pcb_via':
            if g.key(e)==net and not via:
                if kelvin and e['pcb_via_id'] not in kelvin_start_ids:
                    add(draw_layers,g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2).difference(kelvin_target.buffer(.1)))
                continue
            eligible=g.key(e)!=net and soft_eligible(e)
            if via and eligible:continue
            add(draw_layers,g.Point(e['x'],e['y']).buffer(e['outer_diameter']/2),soft=not via and eligible)
        elif typ=='pcb_trace' and (g.key(e)!=net or kelvin):
            if via and '--rip-ordinary-vias' in sys.argv and soft_eligible(e) and g.nets.get(g.key(e)) not in {'GND','PD_VBUS','DATA_VBUS','LOGIC_IN','V3V3','V1V1','VREG','VREF','VCP','BUCK_SW','BUCK_BST','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'}:continue
            for a,b in zip(e['route'],e['route'][1:]):
                if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                    shape=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
                    if kelvin and g.key(e)==net and e['pcb_trace_id'] in kelvin_start_ids:
                        continue
                    if kelvin and g.key(e)==net:
                        shape=shape.difference(kelvin_target.buffer(.1))
                        add([a['layer']],shape)
                    else:add([a['layer']],shape,soft=not via and soft_eligible(e))
        elif typ=='pcb_keepout':
            # Exact circular keepout; native bounding-box diagnostics are independently reconciled.
            # Native DRC applies the 0.15 mm board clearance to keepouts.
            # Retain that extra setback as well as the actual head envelope.
            c=e['center'];r=e['radius'];add(e['layers'],g.Point(c['x'],c['y']).buffer(r,quad_segs=128))
        elif typ=='pcb_hole':
            if e['hole_shape']=='circle':hole=g.Point(e['x'],e['y']).buffer(e['hole_diameter']/2+.1)
            else:
                from shapely.affinity import rotate
                w,h=e['hole_width'],e['hole_height'];dx,dy=((w-h)/2,0) if w>=h else (0,(h-w)/2)
                hole=rotate(g.LineString([(e['x']-dx,e['y']-dy),(e['x']+dx,e['y']+dy)]).buffer(min(w,h)/2+.1),e.get('ccw_rotation',0),origin=(e['x'],e['y']))
            add(draw_layers,hole)
    # Optional construction corridors reserve fanout space for other nets.
    # They do not change the board's actual keepouts or design-rule limits.
    for option in sys.argv:
        if not option.startswith('--avoid-window='):continue
        window_layer,x0,y0,x1,y1=option.split('=',1)[1].split(',')
        assert window_layer in ['top','inner1','inner2','bottom']
        add(draw_layers if via else [window_layer],g.box(float(x0),float(y0),float(x1),float(y1)))
    policy_path=ROOT/'artifacts/v2/routing/usb-routing-plan.json'
    if policy_path.exists():
        policy=json.loads(policy_path.read_text())
        endpoints=[g.Point(c['centerline'][i]) for c in policy['cores'] for i in [0,-1]]
        endpoint_regions=unary_union([p.buffer(1.25) for p in endpoints])
        for core in policy['cores']:
            guard=g.LineString(core['centerline']).buffer(json.loads((ROOT/'src/layer-routing-policy.json').read_text()).get('USB_construction_reference_buffer_mm',policy['reference_corridor_buffer_mm']))
            if via and nets[net]['name']!='GND':
                # All new foreign-net barrels stay outside the trunk reference corridor;
                # paired USB terminal transitions are confined to local fanouts.
                guard=guard
                add(draw_layers,guard)
            elif nets[net]['name']!='GND':add([core['reference_layer']],guard)
    oscillator_path=ROOT/'artifacts/v2/routing/oscillator-plan.json'
    if oscillator_path.exists() and nets[net]['name'] not in ['GND','XIN','XOUT','XTAL_OUT']:
        op=json.loads(oscillator_path.read_text())
        region=unary_union([g.LineString(r['points']).buffer(op['guard_buffer_mm']) for r in op['routes']])
        exempt=unary_union([g.Point(r['points'][0]).buffer(op['MCU_pin_local_exemption_radius_mm']) for r in op['routes'] if r['trace'] in ['oscillator_XIN','oscillator_XOUT']])
        add(draw_layers if via else op['layers_reserved'],region.difference(exempt))
    for l,d in zip(draw_layers,ds):
        b=math.ceil((.52+(current_via_diameter/2 if via else width_for_layer(l)/2))/STEP)
        d.rectangle([0,0,N-1,b],fill=1);d.rectangle([0,N-1-b,N-1,N-1],fill=1)
        d.rectangle([0,0,b,N-1],fill=1);d.rectangle([N-1-b,0,N-1,N-1],fill=1)
    masks=[np.asarray(im,dtype=np.bool_) for im in images]
    if not via:soft_wire=[np.asarray(im,dtype=np.bool_) for im in soft_images]
    return masks

def accessible_pad_points(pad):
    shape=g.geometry(pad);a,b,c,d=shape.bounds
    points={(round(x/STEP)*STEP,round(y/STEP)*STEP) for x in np.arange(a+.025,c,.05) for y in np.arange(b+.025,d,.05)}
    p=g.ports[pad['pcb_port_id']];points.add((p['x'],p['y']))
    return [(x,y) for x,y in points if shape.buffer(-.002).covers(g.Point(x,y))]

repairs=[]
default_order='USB_DP,USB_DM,MCU_DP,MCU_DM,QSPI_SS,QSPI_SCLK,QSPI_SD0,QSPI_SD1,QSPI_SD2,QSPI_SD3,XIN,XOUT,XTAL_OUT,SWCLK,SWDIO,RUN,A_DRV_PLUS,B_DRV_PLUS,A_PLUS,A_MINUS,B_PLUS,B_MINUS,SENSE1,SENSE2,PD_VBUS,LOGIC_IN,BUCK_SW,BUCK_BST,CP1,CP2,VCP,VREG,V3V3,V1V1,I_A_RAW,I_B_RAW,I_A_ADC,I_B_ADC'
net_order=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--net-order=')),default_order).split(',')
for net in sorted(nets,key=lambda k:net_order.index(nets[k]['name']) if nets[k]['name'] in net_order else len(net_order)):
    if nets[net]['name'] in {q.split('=',1)[1] for q in sys.argv if q.startswith('--skip-net=')}:continue
    if '--ground' in sys.argv and nets[net]['name']!='GND':continue
    requested=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--net=')),None)
    if requested and nets[net]['name']!=requested:continue
    if escape_islands and nets[net]['name'] in ['XIN','XOUT','XTAL_OUT']:continue
    if nets[net]['name']=='GND' and '--ground' not in sys.argv:continue  # Regenerate plane returns before any separate ground repair.
    current_width=.3 if nets[net]['name'] in ['A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','V3V3','LOGIC_IN','DATA_VBUS','BUCK_SW','BUZZER_SINK'] else .16
    if nets[net]['name']=='PD_VBUS':current_width=.55
    power=nets[net]['name'] in ['PD_VBUS','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','V3V3','LOGIC_IN','DATA_VBUS','BUCK_SW','BUZZER_SINK','GND']
    if nets[net]['name'] in ['USB_DP','USB_DM','MCU_DP','MCU_DM']:layers=['top','bottom']
    elif nets[net]['name'] in ['PD_VBUS','A_PLUS','B_PLUS','B_MINUS','SENSE1','SENSE2','LOGIC_IN','BUCK_SW','BUCK_BST','CP1','CP2','VCP','VREG','VREF']:layers=['top','inner2','bottom']
    elif nets[net]['name'] in ['QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','QSPI_SS','XIN','XOUT','XTAL_OUT','RUN','SWCLK','SWDIO','USB_DP','USB_DM','MCU_DP','MCU_DM','DIR','STATUS_B_K','LED_B','LED_G','PWR_LED_A','STEP','V3V3','DATA_VBUS','TEMP_SDA','TEMP_SCL','V1V1','GND','DATA_CC1','DATA_CC2','VM_SENSE','ENABLE_N','BOOT_PAD','STATUS_R_C','STATUS_G_C','STATUS_B_C','DCK','DIO']:layers=['top','inner1','inner2','bottom']
    elif nets[net]['name']=='A_MINUS':layers=['top','inner1','inner2','bottom']
    else:layers=['top','inner2','bottom']
    allowed_inner1=json.loads((ROOT/'src/layer-routing-policy.json').read_text())['inner1_allowed_nets']
    if nets[net]['name'] in allowed_inner1 and 'inner1' not in layers:
        layers=['top','inner1','inner2','bottom']
    board=next(e for e in j if e['type']=='pcb_board')
    current_via_diameter=max(board['min_via_pad_diameter'],.5 if nets[net]['name'] in ['PD_VBUS','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'] else .4)
    current_via_hole=max(board['min_via_hole_diameter'],.25 if nets[net]['name'] in ['PD_VBUS','A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','BUZZER_SINK'] else .2)
    override=next((float(q.split('=',1)[1]) for q in sys.argv if q.startswith('--via-pad-mm=')),None)
    if override is not None:
        assert board['min_via_pad_diameter']<=override<=.6 and override-current_via_hole>=.15-1e-9
        current_via_diameter=override
    failed_escape_ports=set()
    failed_start_ports=set()
    for attempt in range(512):
        elems,roots=g.groups(net);islands={}
        for e,r in zip(elems,roots):
            if e.get('pcb_port_id'):islands.setdefault(r,[]).append(e)
        core_roots={r for e,r in zip(elems,roots) if e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('usb_coupled_')}
        usb_net=nets[net]['name'] in ['USB_DP','USB_DM','MCU_DP','MCU_DM']
        if len(set(islands)|core_roots)<2:break
        eligible_roots=None
        if escape_islands:
            through={r for e,r in zip(elems,roots) if e['type'] in ['pcb_via','pcb_plated_hole']}
            eligible_roots=[r for r,ps in islands.items() if r not in through and any(p['pcb_port_id'] not in failed_escape_ports for p in ps)]
            if escape_port:eligible_roots=[r for r in eligible_roots if any(p['pcb_port_id']==escape_port for p in islands[r])]
            if not eligible_roots:break
        bulk_candidates=[r for r,ps in islands.items() if any(p['pcb_port_id'] not in failed_start_ports for p in ps)]
        if not bulk_candidates:break
        if usb_net and core_roots:
            core_geometry=unary_union([g.LineString([(q['x'],q['y']) for q in e['route']]) for e in elems if e['type']=='pcb_trace' and e['pcb_trace_id'].startswith('usb_coupled_')])
            candidates=[r for r in bulk_candidates if r not in core_roots] or bulk_candidates
            startroot=min(candidates,key=lambda r:min(g.geometry(p).distance(core_geometry) for p in islands[r]))
        else:startroot=min(bulk_candidates,key=lambda r:(len(islands[r]),not any(e['type']=='pcb_plated_hole' for e in islands[r])))
        if eligible_roots is not None:startroot=min(eligible_roots,key=lambda r:len(islands[r]))
        requested_start=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--start-ref=')),None)
        if requested_start:
            candidates=[r for r,ps in islands.items() if r in bulk_candidates and any(g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']]==requested_start for p in ps)]
            if not candidates:break
            startroot=min(candidates,key=lambda r:len(islands[r]))
        if nets[net]['name']=='PD_VBUS':
            current_width=.55
            if len(islands[startroot])==1:
                isolated=islands[startroot][0];port=g.ports[isolated['pcb_port_id']];sp=g.sp[port['source_port_id']];reference=g.src[sp['source_component_id']]
                if (reference=='U_DRV' and sp['name'] in ['VBB1','VBB2']) or (reference=='C_VCP' and sp['name']=='pin2') or reference in ['R_PD','C_VM']:current_width=.3
                if reference=='R_VM_H':current_width=.16 # Only the verified high-value voltage-divider terminal.
        if nets[net]['name']=='PD_VBUS':
            refs={g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']] for p in islands[startroot]}
            layers=['top','inner2','bottom']
            if refs and refs<={'U_PD','R_VM_H'}:current_width=.16
            if refs=={'J_PD'}:
                current_width=.3
                layers=['top','bottom'] # Full 0.75 A screened on external copper.
        if nets[net]['name']=='DATA_VBUS':
            refs={g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']] for p in islands[startroot]}
            if refs=={'R_USB_SENSE_H'}:
                assert next(e for e in j if e['type']=='source_component' and e['name']=='R_USB_SENSE_H')['resistance']==100000
                current_width=.16 # Only the physically isolated 100k divider-input terminal; independent branch-cut thermal audit remains mandatory.
        if nets[net]['name']=='V3V3':
            refs={g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']] for p in islands[startroot]}
            load=sum({'U_MCU':.15,'U_FLASH':.03,'U_DRV':.02,'U_TEMP':.001,'BZ1':.12,'R_PWR_LED':.011,'R_TEMP_SDA':.001,'R_TEMP_SCL':.001}.get(ref,0) for ref in refs)
            current_width=.16 if 'L_BUCK' not in refs and load<=.18 else .3
            # The independent physical branch-cut and thermal audit verifies
            # downstream load again on the completed copper, with full-budget fallback.
        if nets[net]['name']=='V3V3':current_width=max(current_width,.2)
        if nets[net]['name'] in ['A_DRV_PLUS','B_DRV_PLUS','A_PLUS','B_PLUS']:
            refs={pad_reference(p) for p in islands[startroot]}
            if refs and refs<={'U_IA','U_IB'}:current_width=.16
        if kelvin:
            assert nets[net]['name'] in ['A_DRV_PLUS','B_DRV_PLUS','A_PLUS','B_PLUS']
            assert requested_start in ['U_IA','U_IB'] and goal_pad_number in [1,2]
            current_width=.16
        phase_bridge=nets[net]['name'] in ['A_DRV_PLUS','B_DRV_PLUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS'] and '--phase-bridges' in sys.argv
        if phase_bridge:layers=['top','inner1','inner2','bottom']
        requested_layers=next((q.split('=',1)[1].split(',') for q in sys.argv if q.startswith('--layers=')),None)
        if requested_layers:
            assert set(requested_layers) and set(requested_layers)<={'top','inner1','inner2','bottom'}
            assert nets[net]['name'] not in ['USB_DP','USB_DM','MCU_DP','MCU_DM']
            layers=requested_layers
        if ('--outer-pd-feeder' in sys.argv and nets[net]['name']=='PD_VBUS') or ('--outer-data-feeder' in sys.argv and nets[net]['name']=='DATA_VBUS'):
            assert set(layers)=={'top','bottom'},'Full-budget 0.30 mm PD feeder requires the 35 um outer layers; thermal audit remains mandatory'
            outer_width=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--outer-feeder-width=')),.3))
            assert .16<=outer_width<=.3
            current_width=outer_width
        goal_ref=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--goal-ref=')),None)
        if kelvin:
            target=next(p for p in j if p['type'] in ['pcb_smtpad','pcb_plated_hole'] and pad_reference(p)==goal_ref and pad_number(p)==goal_pad_number)
            kelvin_target=g.geometry(target)
            # The existing amplifier escape is part of the pickup being extended.
            # Other same-net copper remains blocked except at the shunt land.
            kelvin_start_ids={e[e['type']+'_id'] for e,r in zip(elems,roots) if r==startroot and e['type'] in ['pcb_trace','pcb_via']}
        target_roots={r for r,ps in islands.items() if any(g.src[g.sp[g.ports[p['pcb_port_id']]['source_port_id']]['source_component_id']]==goal_ref for p in ps)} if goal_ref else set()
        if goal_ref and startroot in target_roots:
            print('Requested physical terminal groups joined',nets[net]['name'],requested_start,goal_ref,flush=True);break
        # Use a real connected physical land as the start, never an old location.
        eligible_start=[p for p in islands[startroot] if (not requested_start or pad_reference(p)==requested_start) and (start_pad_number is None or pad_number(p)==start_pad_number)]
        startpad=min(eligible_start,key=lambda e:len(e.get('port_hints',[])))
        startport=g.ports[startpad['pcb_port_id']]
        def failed_attempt():
            # With two islands, an exhausted search already establishes that
            # neither direction has a path through the same obstacle field.
            targets=list(islands.values()) if len(islands)==2 else [islands[startroot]]
            failed_start_ports.update(p['pcb_port_id'] for ps in targets for p in ps)
        traces[net]=next(t['source_trace_id'] for t in j if t['type']=='source_trace' and t.get('subcircuit_connectivity_map_key')==net and startport['source_port_id'] in t.get('connected_source_port_ids',[]))
        sx,sy=startport['x'],startport['y'];startlayer=startpad.get('layer','top')
        start=(*xy(sx,sy),layers.index(startlayer));goals={}
        def goal(x,y,l):
            if l in layers:goals[(*xy(x,y),layers.index(l))]=(x,y)
        for e,r in zip(elems,roots):
            if r==startroot or r not in (set(islands)|core_roots):continue
            if goal_ref and r not in target_roots:continue
            if goal_pad_number is not None and not (e['type'] in ['pcb_smtpad','pcb_plated_hole'] and pad_reference(e)==goal_ref and pad_number(e)==goal_pad_number):continue
            if usb_net and core_roots and r not in core_roots:continue
            if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and e.get('pcb_port_id'):
                p=g.ports[e['pcb_port_id']]
                for l in e.get('layers',[e.get('layer','top')]):
                    for x,y in accessible_pad_points(e):goal(x,y,l)
            elif e['type']=='pcb_via':
                for l in e['layers']:goal(e['x'],e['y'],l)
            elif e['type']=='pcb_copper_pour' and nets[net]['name']=='GND':
                from shapely.geometry import Polygon
                b=e['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
                poly=Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]).buffer(-.01)
                for piece in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:
                    if piece.is_empty or piece.geom_type!='Polygon':continue
                    rp=piece.representative_point();goal(rp.x,rp.y,e['layer'])
                    for ring in [piece.exterior]+list(piece.interiors):
                        for i in range(max(1,math.ceil(ring.length/.15))):
                            q=ring.interpolate(i*.15);goal(q.x,q.y,e['layer'])
            elif e['type']=='pcb_trace':
                if e['pcb_trace_id'].startswith('usb_coupled_'):
                    policy=json.loads((ROOT/'artifacts/v2/routing/usb-routing-plan.json').read_text())
                    track=next(t for c in policy['cores'] for t in c['tracks'] if t['trace_id']==e['pcb_trace_id'])
                    for x,y in [track['points'][0],track['points'][-1]]:goal(x,y,e['route'][0]['layer'])
                    continue
                for a,b in zip(e['route'],e['route'][1:]):
                    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']:
                        count=max(1,math.ceil(math.hypot(b['x']-a['x'],b['y']-a['y'])/.15))
                        for k in range(count+1):goal(a['x']+(b['x']-a['x'])*k/count,a['y']+(b['y']-a['y'])*k/count,a['layer'])
        if escape_islands:goals={start:(sx,sy)}
        if not goals:
            print("UNROUTED: no other physical copper",nets[net]["name"],flush=True);break
        wire=blocked(net);vias=blocked(net,True)
        preferred_layer=next((q.split('=',1)[1] for q in sys.argv if q.startswith('--preferred-layer=')),None)
        if preferred_layer:
            assert preferred_layer in layers
            wire=[m if l==preferred_layer else np.ones_like(m) for l,m in zip(layers,wire)]

        existing={xy(e["x"],e["y"]):e for e in j if e["type"]=="pcb_via" and g.key(e)==net}
        goals={q:v for q,v in goals.items() if not wire[q[2]][q[1],q[0]]}
        if escape_islands and not goals:goals={start:(sx,sy)}
        if not goals:
            print("UNROUTED: no accessible target copper",nets[net]["name"],flush=True)
            failed_attempt();continue
        points=np.array(list(goals));lo=points[:,:2].min(axis=0);hi=points[:,:2].max(axis=0)
        goal_mask=np.ones((N,N),dtype=np.bool_)
        for q in goals:goal_mask[q[1],q[0]]=False
        distance_field=distance_transform_edt(goal_mask)
        search_weight=float(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--search-weight=')),1.5))
        assert 1<=search_weight<=5,'Weighted search affects construction only; all clearance checks remain mandatory'
        search_limit=int(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--max-expanded=')),5000000))
        assert 1000000<=search_limit<=20000000,'Search budget affects construction only'
        heuristic=lambda s:search_weight*float(distance_field[s[1],s[0]])
        starts={(*xy(x,y),layers.index(l)):(x,y) for l in startpad.get('layers',[startpad.get('layer','top')]) if l in layers for x,y in accessible_pad_points(startpad)}
        for anchor,r in zip(elems,roots):
            if r!=startroot:continue
            if anchor['type']=='pcb_via':
                for l in anchor['layers']:
                    if l in layers:starts[(*xy(anchor['x'],anchor['y']),layers.index(l))]=(anchor['x'],anchor['y'])
            elif anchor['type']=='pcb_copper_pour' and nets[net]['name']=='GND':
                # A connected pour is a valid starting conductor, including
                # regions reached through a neck narrower than a new track.
                # Keep the added track's full width inside the existing copper.
                b=anchor['brep_shape'];pts=lambda r:[(p['x'],p['y']) for p in r['vertices']]
                poly=g.Polygon(pts(b['outer_ring']),[pts(r) for r in b.get('inner_rings',[])]).buffer(-.10)
                for piece in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:
                    if piece.is_empty or piece.geom_type!='Polygon':continue
                    rp=piece.representative_point()
                    if anchor['layer'] in layers:
                        starts[(*xy(rp.x,rp.y),layers.index(anchor['layer']))]=(rp.x,rp.y)
                        for ring in [piece.exterior]+list(piece.interiors):
                            for index in range(max(1,math.ceil(ring.length/.15))):
                                q=ring.interpolate(index*.15)
                                starts[(*xy(q.x,q.y),layers.index(anchor['layer']))]=(q.x,q.y)
            elif anchor['type']=='pcb_trace':
                for a,b in zip(anchor['route'],anchor['route'][1:]):
                    if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer'] and a['layer'] in layers:
                        count=max(1,math.ceil(math.hypot(b['x']-a['x'],b['y']-a['y'])/.15))
                        for k in range(count+1):
                            x=a['x']+(b['x']-a['x'])*k/count;y=a['y']+(b['y']-a['y'])*k/count
                            starts[(*xy(x,y),layers.index(a['layer']))]=(x,y)
        starts={q:v for q,v in starts.items() if not wire[q[2]][q[1],q[0]]}
        if escape_islands:
            free_vias=np.logical_not(np.logical_or.reduce(vias))
            for axis,column in [('x',0),('y',1)]:
                coordinates=LOW+np.arange(N)*STEP
                for kind in ['min','max']:
                    value=next((float(q.split('=',1)[1]) for q in sys.argv if q.startswith('--escape-via-'+kind+'-'+axis+'=')),None)
                    if value is None:continue
                    forbidden=coordinates<value-1e-9 if kind=='min' else coordinates>value+1e-9
                    if column==0:free_vias[:,forbidden]=False
                    else:free_vias[forbidden,:]=False
            # The compiled search uses one physical layer and every legal via
            # site as a goal. This replaces the slow Python flood-fill without
            # changing pad, drill, copper or clearance constraints.
            from fast_grid_router import route as fast_route
            layer_index=layers.index(startlayer)
            available=free_vias & ~wire[layer_index]
            ys,xs=np.nonzero(available)
            via_goals=zip(xs,ys,np.zeros(len(xs),dtype=np.int32))
            one_starts={(x,y,0):value for (x,y,l),value in starts.items() if l==layer_index}
            distance=distance_transform_edt(~available)
            local_path,expanded=fast_route([wire[layer_index]],[np.zeros_like(wire[layer_index])],
                vias,{},distance,one_starts,via_goals,1,30,False,[startlayer],limit=500000)
            if local_path is None:
                print('TRAPPED_ESCAPE',nets[net]['name'],pad_reference(startpad),pad_number(startpad),'expanded',expanded,flush=True)
                failed_escape_ports.update(p['pcb_port_id'] for p in islands[startroot]);continue
            path=[(x,y,layer_index) for x,y,_ in local_path];end=path[-1]
            other=next(i for i,l in enumerate(layers) if i!=end[2] and (l=='bottom' if layers[end[2]]=='top' and nets[net]['name'] in ['USB_DP','USB_DM','MCU_DP','MCU_DM'] else True))
            path.append((end[0],end[1],other));end=path[-1];goals={end:world(end)};slim=[path[0]]
        elif '--fast-grid' in sys.argv:
            from fast_grid_router import route as fast_route
            path,expanded=fast_route(wire,soft_wire,vias,existing,distance_field,starts,goals,search_weight,soft_crossing_cost,phase_bridge,layers,limit=search_limit,inner_cost=float(next((q.split("=",1)[1] for q in sys.argv if q.startswith("--inner1-cost=")),1)))
            if path is None:
                print('UNROUTED: no legal grid route',nets[net]['name'],expanded,'start',pad_reference(startpad),pad_number(startpad),flush=True)
                failed_attempt();continue
            end=path[-1]
            slim=[path[0]]
        else:
            heap=[(heuristic(q),0,q) for q in starts];heapq.heapify(heap);best={q:0 for q in starts};prev={};end=None;expanded=0
            while heap:
                _,cost,s=heapq.heappop(heap)
                if cost!=best.get(s):continue
                if s in goals:end=s;break
                expanded+=1
                if expanded>search_limit:break
                x,y,l=s
                options=[(x+dx,y+dy,l,math.sqrt(2) if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]]
                if (x,y) in existing or all(not b[y,x] for b in vias):options.extend((x,y,q,45) for q in range(len(layers)) if q!=l)
                for nx,ny,nl,dc in options:
                    if not(0<=nx<N and 0<=ny<N) or wire[nl][ny,nx]:continue
                    if nl==l and nx!=x and ny!=y and (wire[l][y,nx] or wire[l][ny,x]):continue
                    q=(nx,ny,nl);nc=cost+dc*(12 if phase_bridge and nl==l and layers[nl]=='inner1' else 1)+(soft_crossing_cost if soft_wire[nl][ny,nx] else 0)
                    if nc<best.get(q,float('inf')):best[q]=nc;prev[q]=s;heapq.heappush(heap,(nc+heuristic(q),nc,q))
            if end is None:
                print("UNROUTED: no legal grid route",nets[net]["name"],expanded,flush=True)
                failed_attempt();continue
            path=[end]
            while path[-1] not in starts:path.append(prev[path[-1]])
            path.reverse();slim=[path[0]]
        for k in range(1,len(path)-1):
            a,b,c=path[k-1:k+2]
            if tuple(b[q]-a[q] for q in range(3))!=tuple(c[q]-b[q] for q in range(3)):slim.append(b)
        slim.append(path[-1]);route=[];newvia=[]
        uid=f'{"v2_escape" if escape_islands else "same_side_repair"}_{len(repairs)}_{nets[net]["name"]}_{attempt}'
        used_ids={e.get("pcb_trace_id") for e in j if e["type"]=="pcb_trace"}
        while uid in used_ids or any(e.get("pcb_via_id", "").startswith(uid+"_via_") for e in j):uid+="_rerouted"
        for k,node in enumerate(slim):
            x,y=world(node);l=layers[node[2]]
            if (node[0],node[1]) in existing:x,y=existing[(node[0],node[1])]["x"],existing[(node[0],node[1])]["y"]
            if k and node[2]!=slim[k-1][2]:
                route.append({'route_type':'via','x':x,'y':y,'from_layer':layers[slim[k-1][2]],'to_layer':l,'via_diameter':current_via_diameter,'via_hole_diameter':current_via_hole})
                all_layers=['top','inner1','inner2','bottom'] if board['num_layers']==4 else ['top','bottom']
                v={'type':'pcb_via','pcb_via_id':uid+f'_via_{k}','x':x,'y':y,'outer_diameter':current_via_diameter,'hole_diameter':current_via_hole,'layers':all_layers,'from_layer':'top','to_layer':'bottom','source_net_id':nets[net]['source_net_id'],'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','tented_on_top':True,'tented_on_bottom':True}
                oldvia=next((e for e in j if e['type']=='pcb_via' and math.hypot(e['x']-x,e['y']-y)<.001),None)
                if oldvia:
                    assert g.key(oldvia)==net,'A route cannot reuse a via owned by another net'
                    assert oldvia['from_layer']=='top' and oldvia['to_layer']=='bottom'
                    oldvia['layers']=all_layers
                else:j.append(v);newvia.append([x,y])
            route.append({'route_type':'wire','x':x,'y':y,'layer':l,'width':width_for_layer(l)})
        sx,sy=starts[path[0]];route[0].update(x=sx,y=sy)
        if route[0]['layer'] in startpad.get('layers',[startpad.get('layer','top')]) and g.geometry(startpad).covers(g.Point(sx,sy)):route[0]['start_pcb_port_id']=startpad['pcb_port_id']
        gx,gy=goals[end];route[-1].update(x=gx,y=gy)
        for e in j:
            if e['type'] in ['pcb_smtpad','pcb_plated_hole'] and g.key(e)==net and e.get('pcb_port_id') and route[-1]['layer'] in e.get('layers',[e.get('layer','top')]) and g.geometry(e).buffer(.001).covers(g.Point(gx,gy)):
                route[-1]['end_pcb_port_id']=e['pcb_port_id'];break
        if phase_bridge:
            def inner_length(r):
                return sum(math.dist((a['x'],a['y']),(b['x'],b['y'])) for a,b in zip(r,r[1:]) if a['route_type']==b['route_type']=='wire' and a['layer']==b['layer']=='inner1')
            existing_inner=sum(inner_length(t['route']) for t in j if t['type']=='pcb_trace' and g.key(t)==net)
            proposed_total=existing_inner+inner_length(route)
            limit=json.loads((ROOT/'src/layer-routing-policy.json').read_text())['maximum_total_phase_inner1_length_mm']
            if proposed_total>limit+1e-6:
                # Save the rejected construction candidate for geometry analysis;
                # the saved board and the qualification rule remain unchanged.
                candidate_trace={'type':'pcb_trace','pcb_trace_id':uid,'route':route,'source_net_id':nets[net]['source_net_id'],'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p[k] for p in [route[0],route[-1]] for k in ['start_pcb_port_id','end_pcb_port_id'] if k in p]}
                candidate_vias=[e for e in j if e['type']=='pcb_via' and e['pcb_via_id'].startswith(uid+'_via_')]
                (g.path.parent/('rejected-phase-'+nets[net]['name']+'.json')).write_text(json.dumps({'trace':candidate_trace,'vias':candidate_vias,'existing_inner1_mm':existing_inner,'proposed_total_inner1_mm':proposed_total,'limit_mm':limit},indent=2)+'\n')
                j[:]=[e for e in j if not (e['type']=='pcb_via' and e['pcb_via_id'].startswith(uid+'_via_'))]
                print('UNROUTED: proposed phase transitions exceed total inner1 length budget',nets[net]['name'],proposed_total,limit,flush=True)
                break
        ripped=set()
        # Index foreign wire segments once; keep the same exact clearance and
        # protected-copper assertions while avoiding repeated geometry builds.
        from shapely.strtree import STRtree
        foreign_shapes=[];foreign_owners=[];foreign_layers=[]
        for foreign in j:
            if g.key(foreign)==net:continue
            if foreign['type']=='pcb_via':
                for lname in ['top','inner1','inner2','bottom']:
                    foreign_shapes.append(g.Point(foreign['x'],foreign['y']).buffer(foreign['outer_diameter']/2));foreign_owners.append(foreign);foreign_layers.append(lname)
                continue
            if foreign['type']!='pcb_trace':continue
            for c,d in zip(foreign['route'],foreign['route'][1:]):
                if c['route_type']==d['route_type']=='wire' and c['layer']==d['layer']:
                    foreign_shapes.append(g.LineString([(c['x'],c['y']),(d['x'],d['y'])]).buffer(max(c['width'],d['width'])/2))
                    foreign_owners.append(foreign);foreign_layers.append(c['layer'])
        foreign_index=STRtree(foreign_shapes)
        construction_shapes=[]
        for vnew in j:
            if vnew['type']=='pcb_via' and vnew['pcb_via_id'].startswith(uid+'_via_'):
                for lname in ['top','inner1','inner2','bottom']:construction_shapes.append((lname,g.Point(vnew['x'],vnew['y']).buffer(vnew['outer_diameter']/2)))
        for a,b in zip(route,route[1:]):
            if a['route_type']!=b['route_type'] or a['route_type']!='wire' or a['layer']!=b['layer']:continue
            poly=g.LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(max(a['width'],b['width'])/2)
            construction_shapes.append((a['layer'],poly))
        for lname,poly in construction_shapes:
            for index in foreign_index.query(poly.buffer(.15)):
                if foreign_layers[index]!=lname:continue
                distance=poly.distance(foreign_shapes[index])
                if distance<.15-.000001:
                    foreign=foreign_owners[index];fid=foreign[foreign['type']+'_id']
                    assert soft_eligible(foreign),('Route crosses protected copper',nets[net]['name'],fid,g.nets.get(g.key(foreign)),distance)
                    ripped.add(fid)
        rip_limit=int(next((q.split('=',1)[1] for q in sys.argv if q.startswith('--max-ripped-traces=')),4));assert 0<=rip_limit<=16,'Construction rip-up budget must be between zero and sixteen traces; every displaced net requires full requalification';assert len(ripped)<=rip_limit,('Controlled rip-up budget exceeded',sorted(ripped))
        print('RIP_FOR',nets[net]['name'],sorted(ripped),flush=True)
        ripped_vias={e['pcb_via_id'] for e in j if e['type']=='pcb_via' and e['pcb_via_id'] in ripped}
        retained_fragments=[]
        if '--local-rip' in sys.argv:
            from v2_local_rip import retained_trace_fragments
            dead=[e for e in j if e['type']=='pcb_via' and e['pcb_via_id'] in ripped_vias]
            # Split any trace referring to a removed barrel into real single-layer
            # conductors. A stale annotation must not imply a plated transition.
            for oldtrace in j:
                if oldtrace['type']!='pcb_trace':continue
                affected=oldtrace['pcb_trace_id'] in ripped or any(
                    q['route_type']=='via' and any(math.hypot(q['x']-v['x'],q['y']-v['y'])<1e-6 for v in dead)
                    for q in oldtrace['route'])
                if not affected:continue
                assert soft_eligible(oldtrace),('Removed barrel feeds protected trace',oldtrace['pcb_trace_id'])
                ripped.add(oldtrace['pcb_trace_id'])
                retained_fragments.extend(retained_trace_fragments(oldtrace,construction_shapes,used_ids))
        j[:]=[e for e in j if e.get(e['type']+'_id') not in ripped]
        j.extend(retained_fragments)
        j.append({'type':'pcb_trace','pcb_trace_id':uid,'route':route,'source_net_id':nets[net]['source_net_id'],'source_trace_id':traces[net],'subcircuit_connectivity_map_key':net,'subcircuit_id':'subcircuit_source_group_0','pcb_port_ids':[p[k] for p in [route[0],route[-1]] for k in ['start_pcb_port_id','end_pcb_port_id'] if k in p]})
        repairs.append({'net':nets[net]['name'],'start_port':startpad['pcb_port_id'],'start_mm':[sx,sy],'end_mm':[gx,gy],'vias_mm':newvia,'expanded':expanded,'trace_id':uid,'removed_foreign_trace_ids':sorted(ripped-ripped_vias),'removed_foreign_via_ids':sorted(ripped_vias),'retained_fragment_ids':[e['pcb_trace_id'] for e in retained_fragments]})
        # Rip-up changes the obstacle field and warrants retrying trapped pins.
        # Otherwise continue joining other islands before a later repair pass.
        if ripped:failed_start_ports.clear()
        print(repairs[-1],flush=True)
        for obj in j:
            if obj.get('source_net_id',1) is None:obj.pop('source_net_id')
        g.path.write_text(json.dumps(j,indent=2)+'\n')
        p=repair_log;history=json.loads(p.read_text()) if p.exists() else [];history.append(repairs[-1]);p.write_text(json.dumps(history,indent=2)+'\n')
        if escape_port:break
    else:raise RuntimeError('Repair iteration limit')
g.path.write_text(json.dumps(j,indent=2)+'\n')
p=repair_log;history=json.loads(p.read_text()) if p.exists() else []
history.extend([r for r in repairs if 'removed_for_conservative_native_keepout' in r]);p.write_text(json.dumps(history,indent=2)+'\n')
