// Assembly-only geometry. The electrical board and its supplier CAD stay intact.
// JST SH catalog eSH.pdf: SHR-04V-S, 5 x 2.8 x 5 mm, mated height 6.3 mm.
// The header's native STEP contact row is X=0,1,2,3 / Y=0.35 mm.
export type Point = { x: number; y: number; z: number }
const colors = [[.035,.035,.035],[.03,.45,.12],[.8,.035,.025],[.025,.18,.8]]
const colorNames = ["black", "green", "red", "blue"]
const netNames = ["A_PLUS", "A_MINUS", "B_PLUS", "B_MINUS"]
const point = (x:number,y:number,z:number):Point => ({x,y,z})
const vector = (p:Point) => [p.x,p.y,p.z]
const translate = (p:Point,shape:any) => ({type:"translate",vector:vector(p),shape})
const union = (shapes:any[]) => ({type:"union",shapes})
const colorize = (color:number[],shape:any) => ({type:"colorize",color,shape})

function roundRoute(control:Point[]) {
  const points:Array<Point&{stage:number}>=[]
  const put=(p:Point,stage:number)=>{
    const last=points.at(-1)
    if(!last||Math.hypot(p.x-last.x,p.y-last.y,p.z-last.z)>1e-7)points.push({...p,stage})
  }
  put(control[0],0)
  for(let i=1;i<control.length-1;i++){
    const p=control[i],a=control[i-1],b=control[i+1]
    const before=[p.x-a.x,p.y-a.y,p.z-a.z],after=[b.x-p.x,b.y-p.y,b.z-p.z]
    const la=Math.hypot(...before),lb=Math.hypot(...after)
    const u=before.map(v=>v/la),v=after.map(v=>v/lb),dot=Math.max(-1,Math.min(1,u.reduce((s,a,k)=>s+a*v[k],0)))
    const angle=Math.acos(dot)
    if(angle<1e-5){put(p,i);continue}
    const radius=Math.min(2,Math.min(la,lb)*.4/Math.tan(angle/2)),trim=radius*Math.tan(angle/2)
    const w=v.map((a,k)=>(a-dot*u[k])/Math.sin(angle))
    const start=[p.x-u[0]*trim,p.y-u[1]*trim,p.z-u[2]*trim]
    const center=start.map((a,k)=>a+w[k]*radius)
    const samples=Math.max(3,Math.ceil(angle/(Math.PI/12)))
    for(let j=0;j<=samples;j++){
      const t=j/samples,alpha=t*angle
      const q=center.map((a,k)=>a+radius*(-w[k]*Math.cos(alpha)+u[k]*Math.sin(alpha)))
      put(point(q[0],q[1],q[2]),i-.4+t*.8)
    }
  }
  put(control.at(-1)!,control.length-1)
  return {path:points.map(({stage,...p})=>p),radii:points.slice(1).map((p,i)=>(p.stage+points[i].stage)/2<3.5?.4:.3)}
}

function segment(a:Point,b:Point,radius:number) {
  const dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z,length=Math.hypot(dx,dy,dz)
  return translate(point((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2),{
    // JSCAD plan angles are radians; Circuit JSON CAD rotations are degrees.
    type:"rotate",angles:[0,Math.acos(dz/length),Math.atan2(dy,dx)],
    shape:{type:"cylinder",radius,height:length,segments:16},
  })
}

export function getMotorHarness(board:any[]) {
  const source=board.find(e=>e.type==="source_component"&&e.name==="J_MOTOR")
  if(source?.manufacturer_part_number!=="BM04B-SRSS-TB(LF)(SN)") throw new Error("Unexpected motor header")
  const pcb=board.find(e=>e.type==="pcb_component"&&e.source_component_id===source.source_component_id)
  const cad=board.find(e=>e.type==="cad_component"&&e.source_component_id===source.source_component_id)
  const contacts=board.filter(e=>e.type==="source_port"&&e.source_component_id===source.source_component_id&&e.pin_number>=1&&e.pin_number<=4).sort((a,b)=>a.pin_number-b.pin_number)
  if(contacts.length!==4||contacts.some((p,i)=>p.name!==netNames[i])) throw new Error("Motor pin order changed")
  const angle=cad.rotation.z*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle)
  const world=(x:number,y:number,z:number) => point(
    cad.position.x+c*(x-cad.model_origin_position.x)-s*(y-cad.model_origin_position.y),
    cad.position.y+s*(x-cad.model_origin_position.x)+c*(y-cad.model_origin_position.y),
    cad.position.z+z-cad.model_origin_position.z,
  )
  const boardSurface=board.find(e=>e.type==="pcb_board").thickness/2
  const topZ=boardSurface+6.3,bottomZ=topZ-5
  const headerTopZ=world(1.5,0,4.25).z
  const bodyOrigin=world(1.5,0,0)
  const wirePorts=contacts.map((_,i)=>({...world(i,.35,0),z:topZ}))
  const wires=wirePorts.map((port,i)=>{
    // The furthest contact approaches highest, above the nearer contacts'
    // vertical wire entries. Reversing this order makes the wires intersect.
    // The motor is rotated at its square mounting pattern: local -Y wire
    // outlet faces board +Y, the same edge as J_MOTOR. Loop outside the USB
    // insertion envelope, then approach each contact from directly above.
    const x=(i-1.5)*1.4,side=-9.5-i*1.3,out=22+i*1.5,high=15.5-i*1.25
    const control=[point(x,17.5,-10.75),point(x,out,-10.75),
      point(side,out,-10.75),point(side,out,-8.5),point(side,out,-2.5),
      point(side,out,high),point(port.x,out,high),
      point(port.x,port.y,high),point(port.x,port.y,topZ-.7)]
    const {path,radii}=roundRoute(control)
    return {pin:i+1,net:netNames[i],color:colorNames[i],rgb:colors[i],path,
      splice:{from:point(side,out,-7.5),to:point(side,out,-3.5),radius:.6},
      factory_lead_radius_mm:.4,pigtail_radius_mm:.3,
      segment_radii_mm:radii,
      wire_entry:port,header_contact:world(i,.35,2),
    }
  })
  const wireShapes=wires.flatMap(w=>{
    const shapes=w.path.slice(1).map((b,i)=>segment(w.path[i],b,w.segment_radii_mm[i]))
    shapes.push(...w.path.slice(1,-1).map((p,i)=>translate(p,{type:"sphere",radius:Math.min(w.segment_radii_mm[i],w.segment_radii_mm[i+1]),segments:12})))
    return [colorize(w.rgb,union(shapes)),colorize([.06,.06,.06],segment(w.splice.from,w.splice.to,w.splice.radius))]
  })
  // Only the exposed housing is drawn. The inserted lower 2.96 mm is concealed
  // by the supplier header; this is a catalog outline, not invented latch CAD.
  const housing={type:"subtract",shapes:[
    translate(point(0,0,(headerTopZ+topZ)/2),{type:"cuboid",size:[5,2.8,topZ-headerTopZ]}),
    ...contacts.map((_,i)=>translate(point(i-1.5,.35,(headerTopZ+topZ)/2),{type:"cylinder",radius:.38,height:topZ-headerTopZ+.2,segments:16})),
  ]}
  return {source_component_id:source.source_component_id,pcb_component_id:pcb.pcb_component_id,
    header_mpn:source.manufacturer_part_number,housing_mpn:"SHR-04V-S",contact_mpn:"SSH-003T-P0.2-H",
    pigtail_awg:28,pigtail_insulation_diameter_mm:.6,pitch_mm:1,
    board_surface_z_mm:boardSurface,header_top_z_mm:headerTopZ,housing_bottom_z_mm:bottomZ,housing_top_z_mm:topZ,
    mated_height_mm:6.3,housing_full_dimensions_mm:[5,2.8,5],
    body_origin:bodyOrigin,body_rotation_z:cad.rotation.z,wires,
    // Separate native CAD parts retain per-conductor colors through GLTF export;
    // boolean-unioning differently colored solids discards those material colors.
    wirePlans:wireShapes.filter((_,i)=>i%2===0),splicePlans:wireShapes.filter((_,i)=>i%2===1),
    housingPlan:colorize([.93,.93,.88],housing),
    motor_exit_board_side:"+Y",motor_local_wire_side:"-Y",motor_mount_rotation_anchor:"topedge",
    motor_termination:"permanent factory leads; no motor-side connector",
    cable_construction:"Factory leads shortened and joined through four insulated splices to a 28 AWG JST-SH pigtail",
    factory_lead_diameter_is_an_unqualified_visual_envelope:true,
  }
}
