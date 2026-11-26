/** Frozen driver failure diagnostic. Stricter routing target; board rules unchanged. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
import {AutoroutingPipelineSolver,AUTOROUTER_VERSION} from '@tscircuit/capacity-autorouter'
const extraPadReserve=process.env.PAD_CORRIDOR==='1';const dir=extraPadReserve?'.config/integration/driver-corridor':'.config/integration/driver-margin';mkdirSync(dir,{recursive:true})
const original=JSON.parse(readFileSync('artifacts/iteration-2/driver-reduced-input.srj.json','utf8'))
const input={...original,minTraceToPadEdgeClearance:.20,obstacles:original.obstacles.map((o:any)=>extraPadReserve&&o.circuitJsonMetadata?.pcb_smtpad_id==='pcb_smtpad_227'?{...o,width:o.width+.24,height:o.height+.24}:o)}
writeFileSync(dir+'/experiment-input.srj.json',JSON.stringify(input,null,2)+'\n')
const s:any=new AutoroutingPipelineSolver(input,{effort:2});const started=performance.now();let exception
try{while(!s.solved&&!s.failed&&performance.now()-started<60000)s.step()}catch(e){exception=String(e)}
const result={diagnostic_only:true,extra_C_VCP_pin1_forbidden_border_mm:extraPadReserve?.12:0,frozen_prior_geometry:true,new_bottom_placement_trial:false,solver_version:AUTOROUTER_VERSION,original_spacing_target_mm:original.minTraceToPadEdgeClearance,stricter_router_spacing_target_mm:.20,unchanged_board_clearance_gate_mm:.15,all_obstacles_retained:input.obstacles.length===original.obstacles.length,connections:input.connections.length,solved:s.solved,failed:s.failed,error:s.error,exception,phase:s.getCurrentPhase?.(),elapsed_ms:performance.now()-started}
writeFileSync(dir+'/result.json',JSON.stringify(result,null,2)+'\n');if(s.solved)writeFileSync(dir+'/output.srj.json',JSON.stringify(s.getOutputSimpleRouteJson(),null,2)+'\n');console.log(result)
