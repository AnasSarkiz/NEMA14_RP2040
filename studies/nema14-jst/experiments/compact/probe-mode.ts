/** Targeted saved-input probes, not a new aggregate routing attempt. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
import {gunzipSync} from 'node:zlib'
import {AutoroutingPipelineSolver,AUTOROUTER_VERSION} from '@tscircuit/capacity-autorouter'
const raw=JSON.parse(gunzipSync(readFileSync('artifacts/iteration-4/normal-attempt.circuit.json.routing-input.json.gz')).toString()).simpleRouteJson
const net=raw.connections.find((c:any)=>c.name==='source_net_2'),out='artifacts/iteration-5/mode-probes';mkdirSync(out,{recursive:true})
for(const [name,ids] of [['old-pair',['pcb_port_213','pcb_port_214']],['adjacent-mode',['pcb_port_211','pcb_port_212']],['via-to-vdd',['pcb_port_387','pcb_port_217']],['driver-mode-island',['pcb_port_211','pcb_port_212','pcb_port_213','pcb_port_214','pcb_port_217','pcb_port_387']]] as const){
 const srj={...raw,connections:[{...net,pointsToConnect:net.pointsToConnect.filter((p:any)=>(ids as readonly string[]).includes(p.pcb_port_id))}]};const s:any=new AutoroutingPipelineSolver(srj,{effort:2}),start=performance.now();let exception
 try{while(!s.solved&&!s.failed&&performance.now()-start<20000)s.step()}catch(e){exception=String(e)}
 const q=s.portPointPathingSolver?.tinyPipelineSolver?.solveGraph,blocked=q?.getStaticallyUnroutableRoutes?.();const r={name,solver_version:AUTOROUTER_VERSION,solved:s.solved,failed:s.failed,error:s.error,exception,phase:s.getCurrentPhase?.(),elapsed_ms:performance.now()-start,obstacles:srj.obstacles.length,all_preloaded_copper_retained:srj.traces.length===raw.traces.length,preloaded_traces:srj.traces.length,ports:ids,statically_unroutable:blocked};writeFileSync(out+'/'+name+'.json',JSON.stringify(r,null,2)+'\n');writeFileSync(out+'/'+name+'.input.json',JSON.stringify(srj,null,2)+'\n');if(s.solved)writeFileSync(out+'/'+name+'.output.json',JSON.stringify(s.getOutputSimpleRouteJson(),null,2)+'\n');console.log(r)
}
