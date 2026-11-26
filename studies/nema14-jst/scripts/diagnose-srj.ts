/** Isolated native SRJ diagnostics. Never installs experimental copper in the board source. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
import {createHash} from 'node:crypto'
import {getSimpleRouteJsonFromCircuitJson} from '@tscircuit/core'
import {AutoroutingPipelineSolver, AUTOROUTER_VERSION} from '@tscircuit/capacity-autorouter'
const input=process.argv[2],out=process.argv[3],mode=process.argv[4]??'export'
if(!input||!out)throw Error('Usage: bun scripts/diagnose-srj.ts circuit.json output-directory [export|driver|kelvin|usb|full]')
mkdirSync(out,{recursive:true});const bytes=readFileSync(input),json=JSON.parse(bytes.toString()),board=json.find((e:any)=>e.type==='pcb_board')
const {simpleRouteJson:srj}=getSimpleRouteJsonFromCircuitJson({circuitJson:json,subcircuit_id:board.subcircuit_id,minTraceWidth:board.min_trace_width,minTraceToPadEdgeClearance:board.min_trace_to_pad_edge_clearance,minPadEdgeToPadEdgeClearance:board.min_pad_edge_to_pad_edge_clearance,minBoardEdgeClearance:board.min_board_edge_clearance,minViaHoleDiameter:board.min_via_hole_diameter,minViaPadDiameter:board.min_via_pad_diameter,minViaHoleEdgeToViaHoleEdgeClearance:board.min_via_hole_edge_to_via_hole_edge_clearance,minPlatedHoleDrillEdgeToDrillEdgeClearance:board.min_plated_hole_drill_edge_to_drill_edge_clearance})
writeFileSync(out+'/native-input.srj.json',JSON.stringify(srj,null,2)+'\n')
const src=new Map(json.filter((e:any)=>e.type==='source_component').map((e:any)=>[e.source_component_id,e.name]));const sp=new Map(json.filter((e:any)=>e.type==='source_port').map((e:any)=>[e.source_port_id,e]));const pp=new Map(json.filter((e:any)=>e.type==='pcb_port').map((e:any)=>[e.pcb_port_id,e]))
console.log(JSON.stringify({connections:srj.connections.length,obstacles:srj.obstacles.length}))
if(mode==='export')process.exit(0)
const sets:Record<string,Set<string>>={driver:new Set(['U_DRV','C_CP','C_VCP','C_VREG','C_VM','C_DRV_LOGIC','C_BULK','R_SA','R_SB']),kelvin:new Set(['U_DRV','R_SHUNT_A','R_SHUNT_B','U_IA','U_IB','C_IA','C_IB','J_MOTOR']),usb:new Set(['U_MCU','R_DM','R_DP','U_ESD','J_DATA'])}
const allowed=sets[mode]
const pointName=(p:any)=>{const port:any=pp.get(p.pcb_port_id);const s:any=sp.get(port?.source_port_id);return s?`${src.get(s.source_component_id)}.${s.name}`:null}
const nets=json.filter((e:any)=>e.type==='source_net');const netNames=new Map(nets.map((e:any)=>[e.source_net_id,e.name]));const byKey=new Map(nets.map((e:any)=>[e.subcircuit_connectivity_map_key,e.name]));
const connectionNet=(c:any)=>{if(netNames.has(c.name))return netNames.get(c.name);const first:any=c.pointsToConnect[0];const port:any=pp.get(first?.pcb_port_id);const source:any=sp.get(port?.source_port_id);return byKey.get(source?.subcircuit_connectivity_map_key)}
const wanted:Record<string,Set<string>>={driver:new Set(['CP1','CP2','VCP','VREG','PD_VBUS','V3V3','GND','SENSE1','SENSE2']),kelvin:new Set(['A_DRV_PLUS','A_PLUS','B_DRV_PLUS','B_PLUS','V3V3','GND']),usb:new Set(['MCU_DM','MCU_DP','USB_DM','USB_DP','GND','DATA_VBUS'])}
let filtered:any={...srj}
if(mode!=='full')filtered.connections=srj.connections.map(c=>({...c,pointsToConnect:c.pointsToConnect.filter((p:any)=>{const ref=pointName(p);return ref&&allowed.has(ref.split('.')[0])})})).filter((c:any)=>c.pointsToConnect.length>=2&&wanted[mode].has(connectionNet(c) as string))
writeFileSync(out+'/experiment-input.srj.json',JSON.stringify(filtered,null,2)+'\n')
const metadata:any={source_sha256:createHash('sha256').update(bytes).digest('hex'),mode,autorouter_version:AUTOROUTER_VERSION,input_connections:srj.connections.length,experiment_connections:filtered.connections.length,all_native_obstacles_retained:filtered.obstacles.length===srj.obstacles.length,experimental_only:true,full_board_routed:false,physical_kelvin_verified:false,usb_return_plane_verified:false}
let solver:any
try{
 solver=new AutoroutingPipelineSolver(filtered,{effort:2});const started=performance.now();let checkpoint=0;metadata.state='running';metadata.nominal_step_loop_budget_ms=60000;writeFileSync(out+'/result.json',JSON.stringify(metadata,null,2)+'\n');while(!solver.solved&&!solver.failed&&performance.now()-started<60000){if(performance.now()-checkpoint>500){metadata.elapsed_ms=performance.now()-started;metadata.phase=solver.getCurrentPhase?.();writeFileSync(out+'/result.json',JSON.stringify(metadata,null,2)+'\n');checkpoint=performance.now()}solver.step()}metadata.state=solver.solved?'solved':solver.failed?'failed':'step_loop_budget_exhausted'
 metadata.elapsed_ms=performance.now()-started;metadata.solved=solver.solved;metadata.failed=solver.failed;metadata.error=solver.error;metadata.phase=solver.getCurrentPhase?.()
 if(solver.solved){const output=solver.getOutputSimpleRouteJson();writeFileSync(out+'/output.srj.json',JSON.stringify(output,null,2)+'\n');metadata.output_trace_count=output.traces?.length??0}
}catch(error){metadata.exception=String(error)}
writeFileSync(out+'/result.json',JSON.stringify(metadata,null,2)+'\n');console.log(JSON.stringify(metadata,null,2))
