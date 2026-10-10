/** Native tscircuit routing attempt for revised nets; accepted copper is input geometry. */
import {getSimpleRouteJsonFromCircuitJson} from '@tscircuit/core'
import {AutoroutingPipelineSolver} from '@tscircuit/capacity-autorouter'
import{readFileSync,writeFileSync}from'node:fs'
const j=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
const n=new Map(j.filter((e:any)=>e.type==='source_net').map((e:any)=>[e.source_net_id,e.name]))
const input:any=getSimpleRouteJsonFromCircuitJson({circuitJson:j,minTraceWidth:.16,minTraceToPadEdgeClearance:.15,minViaHoleDiameter:.25,minViaPadDiameter:.5,minBoardEdgeClearance:.3,subcircuit_id:'subcircuit_source_group_0'}).simpleRouteJson
const keep=new Set(['GND','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2','PD_CC1','PD_CC2','PD_LEGACY_DATA','DATA_CC1','DATA_CC2','PD_VDD'])
input.connections=input.connections.filter((c:any)=>!keep.has(n.get(c.name) as string))
writeFileSync('artifacts/validation/diagnostics-native-input.json',JSON.stringify(input,null,2))
const solver=new AutoroutingPipelineSolver(input,{effort:2})
let last='',t=Date.now();const started=t
let caught:string|null=null
try {
while(!solver.solved&&!solver.failed&&Date.now()-started<120000){
 const end=Date.now()+100;while(Date.now()<end&&!solver.solved&&!solver.failed)solver.step()
 const phase=solver.getCurrentPhase();if(phase!==last||Date.now()-t>15000){console.log(phase,solver.iterations,solver.computeProgress());last=phase;t=Date.now()}
 await new Promise(resolve=>setTimeout(resolve,0))
}
} catch (error) {caught=error instanceof Error?error.message:String(error)}
const status={solved:solver.solved,failed:solver.failed,error:caught??solver.error??null,durationMs:Date.now()-started};console.log(status)
writeFileSync('artifacts/validation/diagnostics-native-attempt.json',JSON.stringify(status,null,2))
if(solver.solved)writeFileSync('artifacts/validation/diagnostics-native-output.json',JSON.stringify(solver.getOutputSimpleRouteJson(),null,2))
else process.exitCode=1
