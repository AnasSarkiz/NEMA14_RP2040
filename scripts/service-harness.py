"""Drawing-derived HAR-001 harness and carrier attachment; no measured fit claims.

JST PH dimensions are taken from references/JST-PH.pdf. PHR-4/contact profiles
are engineering installation envelopes, not factory spring-contact CAD. External PHR dimensions9.8x4.5x6.85 per JST; contact envelope1.5x2.08x5.7.
"""
import cadquery as cq
import math,itertools
import numpy as np
from numpy.polynomial import Polynomial as P

def build(carrier,pcb_parts,records,front):
    box=lambda w,h,d,x=0,y=0,z=0:cq.Workplane('XY').box(w,h,d).val().translate((x,y,z))
    cyl=lambda r,h,x,y,z:cq.Workplane('XY').circle(r).extrude(h).val().translate((x,y,z))
    motor=next(e for e in records if e['type']=='pcb_component' and any(s['type']=='source_component' and s['source_component_id']==e['source_component_id'] and s['name']=='J_MOTOR' for s in records))
    mx,my=motor['center']['x'],motor['center']['y']
    pcb_mounts=[(e['x'],e['y'])for e in records if e['type']=='pcb_hole'and e.get('hole_diameter')==3.2]
    # Metal supports end at -1.8; 1 mm PEEK supports isolate PCB underside -0.8.
    for x,y in pcb_mounts:
        carrier=carrier.cut(box(5,5,1.001,x,y,-1.2995))
    # Two rear side brackets support a crossbar and screw-fastened cable clamp.
    for x in [-21.6,21.6]:
        carrier=carrier.fuse(box(6,40,4,x,-29,-4.8))
    carrier=carrier.fuse(box(49.2,14,4,0,-42,-4.8))
    for x in [-9,9]:carrier=carrier.cut(cyl(1.025,5,x,-42,-7.3))
    # Host attachment on outside rails; front motor fasteners remain separate.
    for x,y in itertools.product([-21.6,21.6],[-13,13]):
        carrier=carrier.fuse(cyl(3,4,x,y,front-8))
        carrier=carrier.cut(cyl(1.25,6,x,y,front-8))
    carrier=carrier.cut(cyl(5,5,0,-42,-7.3))
    extra={};colors={};hardware={};heads={};wire_paths=[]
    for i,(x,y) in enumerate(pcb_mounts):
        support=cyl(2.25,1,x,y,-1.8).cut(cyl(1.35,1.02,x,y,-1.81))
        collar=cyl(3.25,.49,x,y,-2.29).cut(cyl(2.30,.51,x,y,-2.30))
        washer=cyl(2.25,.5,x,y,.8).cut(cyl(1.35,.52,x,y,.79))
        extra[f'PEEK_support_{i}']=support.fuse(collar)
        extra[f'PEEK_top_washer_{i}']=washer
        head=cyl(2.25,2.5,x,y,1.3);heads[f'PCB_M2p5_head_{i}']=head
        hardware[f'PCB_M2p5x8_{i}']=head.fuse(cyl(1.25,8,x,y,-6.7))
    # Nomex 410 0.51 mm sheet, positive capture at four collars; no adhesive.
    barrier=box(35,40,.51,0,-2.5,-2.545)
    for x,y in pcb_mounts:barrier=barrier.cut(cyl(2.4,1,x,y,-3))
    extra['Nomex410_INS001']=barrier
    # PEEK two-piece clamp with elastomer liner, fixed by two M2.5 screws.
    clamp=box(24,14,6,0,-42,.2).cut(cyl(5.5,6.2,0,-42,-2.9))
    for x in [-9,9]:
        clamp=clamp.cut(cyl(1.35,6.2,x,-42,-2.9))
        hardware[f'Clamp_M2p5x10_{x}']=cyl(2.25,2.5,x,-42,3.2).fuse(cyl(1.25,10,x,-42,-6.8))
    extra['PEEK_clamp_left']=clamp.intersect(box(12,16,8,-6,-42,.2))
    extra['PEEK_clamp_right']=clamp.intersect(box(12,16,8,6,-42,.2))
    liner=cyl(5.5,6,0,-42,-2.8)
    axes=[(-3.5,-42-1.3),(-3.5,-42+1.3),(3.5,-42-1.3),(3.5,-42+1.3)]
    for bx,by in axes:liner=liner.cut(cyl(.475,6.2,bx,by,-2.9))
    extra['Clamp_silicone_liner']=liner
    # Installed header: trim pins to <=0.8 below PCB underside before insulation.
    untrimmed=pcb_parts['J_MOTOR']
    pcb_parts['J_MOTOR']=untrimmed.intersect(box(100,100,100,0,0,48.4))
    # PHR-4 full external dimensions, two-level nose; this is drawing-derived.
    plug=box(9.8,4.5,2,mx,my-.65,7.8)
    nose=box(7.8,2.5,4.85,mx,my-.65,4.375)
    for dx in [-3,-1,1,3]:nose=nose.cut(box(.85,1.0,5,mx+dx,my,4.35))
    extra['PHR4_mating_housing_envelope']=plug.fuse(nose)
    for i,dx in enumerate([-3,-1,1,3]):
        x=mx+dx
        # Contact and sleeve envelopes preserve color/pin positions and show tails.
        contact=box(1.5,2.08,5.7,x,my,5.95).cut(box(.5,.6,4.9,x,my,5.55))
        extra[f'SPH002_contact_{i+1}']=contact
        tail=cyl(1,.9,x,my,-1.7).cut(cyl(.9,.81,x,my,-1.6))
        extra[f'Insulated_solder_tail_{i+1}']=tail
        # Belden83004 AWG24 PTFE, nominalOD1.1mm; published minimum bend11mm.
        bx,by=axes[i];R=12.;a=cq.Vector(x,my,30);b=cq.Vector(x,my-2*R,30)
        edges=[cq.Edge.makeLine(cq.Vector(x,my,8.8),a),cq.Edge.makeThreePointArc(a,cq.Vector(x,my-R,30+R),b)]
        controls=[b,cq.Vector(x,my-24,21.333333),cq.Vector(bx,by,12.666667),cq.Vector(bx,by,4)]
        transition=cq.Edge.makeBezier(controls);edges += [transition,cq.Edge.makeLine(cq.Vector(bx,by,4),cq.Vector(bx,by,-9+(by+42)*1.5/1.3))]
        z0=-9+(by+42)*1.5/1.3;a=cq.Vector(bx,by,z0);b=cq.Vector(bx,by+R,z0-R)
        edges.append(cq.Edge.makeThreePointArc(a,cq.Vector(bx,by+R-R/math.sqrt(2),z0-R/math.sqrt(2)),b))
        end=cq.Vector(bx,-19.5,z0-R);edges.append(cq.Edge.makeLine(b,end))
        # HAR002 insulated factory-lead lap splice at this endpoint. Factory AWG
        # is undocumented: cut/strip/splice acceptance remains a measured gate.
        extra[f'Splice_insulation_{i+1}']=box(2.8,8,2.8,bx,-23.5,z0-R)
        solids=[]
        for edge in edges:
            tangent=edge.tangentAt(0);plane=cq.Plane(origin=edge.startPoint(),normal=tangent)
            solids.append(cq.Workplane(plane).circle(.55).sweep(cq.Wire.assembleEdges([edge]),isFrenet=True).val())
        wire=cq.Compound.makeCompound(solids);extra[f'Wire_{i+1}']=wire
        c=np.array([v.toTuple()for v in controls]);polys=[P([c[0,k],3*(c[1,k]-c[0,k]),3*(c[0,k]-2*c[1,k]+c[2,k]),-c[0,k]+3*c[1,k]-3*c[2,k]+c[3,k]])for k in range(3)]
        dp=[v.deriv()for v in polys];dd=[v.deriv()for v in dp];cross=[dp[1]*dd[2]-dp[2]*dd[1],dp[2]*dd[0]-dp[0]*dd[2],dp[0]*dd[1]-dp[1]*dd[0]];A=sum(v*v for v in dp);B=sum(v*v for v in cross);stationary=B.deriv()*A-3*B*A.deriv();samples=[0.,1.]+[float(v.real)for v in stationary.roots()if abs(v.imag)<1e-7 and 0<=v.real<=1];radius=min(math.sqrt(A(t)**3/B(t))for t in samples if B(t)>1e-16);assert radius>=11,(i,radius)
        wire_paths.append({'pin':i+1,'clamp_axis_mm':[bx,by],'loop_radius_mm':12,'upper_transition_bezier_control_mm':[v.toTuple() for v in controls],'lower_return_radius_mm':12,'upper_transition_exact_cubic_min_radius_mm':radius,'upper_transition_extremum_parameters':samples,'curve_length_mm':sum(e.Length() for e in edges),'manufacturer_minimum_bend_radius_mm':11})
        colors[f'Wire_{i+1}']=[(.08,.08,.09),(.05,.55,.15),(.85,.07,.06),(.05,.25,.85)][i]
        colors[f'Insulated_solder_tail_{i+1}']=colors[f'Wire_{i+1}']
    # Extend the four actual native motor-CAD lead-stub endpoints. OD is model
    # evidence only, not an inferred wire gauge/temperature procurement rating.
    native_leads=[(-1.102824,23.705067),(-1.102824,24.794933),(1.102824,23.705067),(1.102824,24.794933)]
    factory_paths=[]
    for i,(fx,fz) in enumerate(native_leads):
        bx,by=axes[i];z0=front+fz;endz=-9+(by+42)*1.5/1.3-12
        lane=(-4.8,-2.2,4.8,2.2)[i]
        start=cq.Vector(fx,-35.6,z0);a=cq.Vector(lane,-57.6,z0);b=cq.Vector(lane,-57.6,z0-24)
        controls=[b,cq.Vector(lane,-48.9,z0-24),cq.Vector(lane,-40.2,endz-1.5),cq.Vector(lane,-31.5,endz-1.5)]
        fan=[start,cq.Vector(fx,-42.933333,z0),cq.Vector(lane,-50.266667,z0),a]
        lap=[controls[-1],cq.Vector(lane,-27.5,endz-1.5),cq.Vector(bx,-23.5,endz),cq.Vector(bx,-19.5,endz)]
        edges=[cq.Edge.makeBezier(fan),cq.Edge.makeThreePointArc(a,cq.Vector(lane,-69.6,z0-12),b),cq.Edge.makeBezier(controls),cq.Edge.makeBezier(lap)]
        solids=[]
        for edge in edges:solids.append(cq.Workplane(cq.Plane(origin=edge.startPoint(),normal=edge.tangentAt(0))).circle(.472613).sweep(cq.Wire.assembleEdges([edge]),isFrenet=True).val())
        extra[f'FactoryLead_{i+1}']=cq.Compound.makeCompound(solids);colors[f'FactoryLead_{i+1}']=colors[f'Wire_{i+1}']
        factory_paths.append({'pin':i+1,'native_cad_stub_endpoint_mm':[fx,-35.6,fz],'world_splice_mm':[bx,-23.5,endz],'nominal_model_od_mm':.945226,'curve_length_after_stub_mm':sum(e.Length()for e in edges),'original_factory_lead_length_mm':[290,310],'cubic_controls_mm':[v.toTuple()for v in controls],'routing_radius_mm':12,'factory_wire_actual_gauge_od_bend_temperature_not_assumed':True})
    # Whole plug/gripping access, 10 mm withdrawal, above the shroud mouth.
    access=box(12,7,16,mx,my-.65,14.8)
    report={
        'connector':'JST B4B-PH-K-S(LF)(SN), C131334; exact native STEP retained',
        'splice_insulation_candidate':'TE Raychem RT-375-1/8-X, procurement/temperature/dimensions certificate required; recovered assemblyOD<=2.8mm envelope','housing':'JST PHR-4','contacts':'4 x JST SPH-002T-P0.5S',
        'wire_acceptance':{'awg':'30..24','insulation_od_mm':[.8,1.5],'harness_nominal_od_mm':1.1,'selected_wire':'Belden83004 AWG24 PTFE 200C; see manufacturer reference','clamp_accepted_od_mm':[1.05,1.20],'wire_temperature_rating_required_c':150},
        'wire_paths':wire_paths,'factory_lead_paths':factory_paths,'factory_lead_color_assignment':'Nominal fanout only; identify actual colors/windings by continuity, not CAD arrangement.','clamp_through_carrier_clearance_bore_mm':10.0,'clamp_liner_outer_diameter_mm':11.0,'clamp_liner_four_bores_mm':.95,'clamp_bore_tolerance_mm':.05,'maximum_bundle_diameter_mm':2*math.sqrt(3.5**2+1.3**2)+1.2,'harness_drawing':'HAR-001','service_loop_radius_mm':12,'unplug_withdrawal_mm':10,
        'clamp_body_mm':[24,14,6],'clamp_seating_z_mm':-2.8,'clamp_screw_nominal_metal_engagement_mm':4,'positive_restraint':'HC-001 two-piece PEEK clamp, silicone liner, two M2.5x10 screws into carrier crossbar; pull test unperformed',
        'insulation':'INS-001 Nomex410 0.51mm, material certificate >=150C required; INS-002 PEEK supports/washers; 125C minimum tail insulation; certificates required',
        'solder_tail_max_below_pcb_mm':.8,'solder_fillet_max_below_pcb_mm':.5,
        'nominal_tail_to_barrier_mm':.59,'tail_to_barrier_after_0p15_pcb_0p05_carrier_0p05_sheet_allowances_mm':.34,
        'carrier_material':'6061-T6/T651; machining +/-0.05mm',
        'host_mount':{'thread':'4 x M3, minimum6mm available depth; use4.5..5.5mm engagement','centers_mm':[[x,y] for x,y in itertools.product([-21.6,21.6],[-13,13])],'front_standoff_mm':8.0,'shaft_exposure_beyond_host_plane_mm':[14.9,17.1]},
        'factory_cad_for_mating_plug_and_contacts':False,
        'limitations':['PHR/contact profile is drawing-derived, internal spring/key fit requires actual parts.','Wire and solder shapes are installation envelopes; no crimp/solder/pull measurement.','Cable STEP and maximum envelope evaluated separately; physical fit and bend life remain unperformed.','No structural, thermal, material certificate or physical-fit qualification claimed.']
    }
    return carrier.clean(),extra,colors,hardware,heads,access,report
