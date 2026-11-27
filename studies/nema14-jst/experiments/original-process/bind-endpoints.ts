/** Attach logical terminals only after geometric stroke/pad or stroke/annulus contact.
 * No copper, width, net, or endpoint coordinate is changed. */
import paths from './paths.json'
import vias from './vias.json'
export function bindEndpoints(root:any,traceSpecs:any[]=paths,viaSpecs:Record<string,any>=vias){
 const j=root.getCircuitJson(),sources=new Map(j.filter((e:any)=>e.type==='source_trace').map((e:any)=>[e.source_trace_id,e])),components=new Map(j.filter((e:any)=>e.type==='source_component').map((e:any)=>[e.source_component_id,e.name]));const annotations:any[]=[];
 function terminal(selector:string){const [name,pin]=selector.slice(1).split(' > .');const vs=viaSpecs[name];let port:any,pad:any;
  if(vs){pad=j.find((v:any)=>v.type==='pcb_via'&&Math.hypot(v.x-vs.x,v.y-vs.y)<1e-8);port=j.find((p:any)=>p.type==='pcb_port'&&pad.pcb_port_ids.includes(p.pcb_port_id)&&j.some((s:any)=>s.type==='source_port'&&s.source_port_id===p.source_port_id&&s.name===pin))}
  else{const sp=j.find((e:any)=>e.type==='source_port'&&components.get(e.source_component_id)===name&&e.name===pin);port=j.find((e:any)=>e.type==='pcb_port'&&e.source_port_id===sp?.source_port_id);pad=j.find((e:any)=>e.type==='pcb_smtpad'&&e.pcb_port_id===port?.pcb_port_id)}
  if(!port||!pad)throw Error('Missing actual terminal '+selector);return {port,pad};
 }
 function contact(n:any,p:any){const radius=n.width/2;if(p.type==='pcb_via'){const d=Math.hypot(n.x-p.x,n.y-p.y);return p.layers.includes(n.layer)&&d-radius<p.outer_diameter/2-1e-8&&d+radius>p.hole_diameter/2+1e-8}
  if(p.layer!==n.layer) return false;const angle=-(p.ccw_rotation??0)*Math.PI/180,dx=n.x-p.x,dy=n.y-p.y,x=dx*Math.cos(angle)-dy*Math.sin(angle),y=dx*Math.sin(angle)+dy*Math.cos(angle);let distance:number;
  if(['pill','rotated_pill'].includes(p.shape)){const r=Math.min(p.width,p.height)/2;distance=Math.max(0,Math.hypot(Math.max(Math.abs(x)-(p.width/2-r),0),Math.max(Math.abs(y)-(p.height/2-r),0))-r)}
  else if(p.shape==='rect')distance=Math.hypot(Math.max(Math.abs(x)-p.width/2,0),Math.max(Math.abs(y)-p.height/2,0));else throw Error('Unverified terminal pad shape '+p.shape);
  return distance<radius-1e-8;
 }
 for(const p of traceSpecs){const t=j.find((e:any)=>e.type==='pcb_trace'&&(sources.get(e.source_trace_id) as any)?.name===p.name);if(!t)throw Error('Missing physical trace '+p.name);const s:any=sources.get(t.source_trace_id);const route=t.route.map((q:any)=>({...q}));
  for(const [selector,node,field] of [[p.from,route[0],'start_pcb_port_id'],[p.to,route.at(-1),'end_pcb_port_id']] as any[]){const {port,pad}=terminal(selector);if(!s.connected_source_port_ids.includes(port.source_port_id)||!contact(node,pad))throw Error('Unproven terminal stroke contact '+p.name+' '+selector);node[field]=port.pcb_port_id;annotations.push({trace:p.name,terminal:selector,physical_port:port.pcb_port_id,point_mm:[node.x,node.y],geometry_changed:false})}
  root.db.pcb_trace.update(t.pcb_trace_id,{route});
 }
 return annotations;
}
