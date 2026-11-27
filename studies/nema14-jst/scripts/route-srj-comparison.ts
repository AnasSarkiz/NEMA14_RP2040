/** Bounded local native SRJ comparison; no saved board copper is modified. */
import {readFileSync,writeFileSync} from 'node:fs'
import {AutoroutingPipelineSolver,AUTOROUTER_VERSION} from '@tscircuit/capacity-autorouter'
const input=process.argv[2],out=process.argv[3],srj=JSON.parse(readFileSync(input,'utf8')),s:any=new AutoroutingPipelineSolver(srj,{effort:2}),start=performance.now();let exception
try{while(!s.solved&&!s.failed&&performance.now()-start<60000)s.step()}catch(e){exception=String(e)}
const result={comparison_only:true,autorouter_version:AUTOROUTER_VERSION,solved:s.solved,failed:s.failed,error:s.error,exception,phase:s.getCurrentPhase?.(),elapsed_ms:performance.now()-start};writeFileSync(out,JSON.stringify(result,null,2)+'\n');if(s.solved)writeFileSync(out+'.output.srj.json',JSON.stringify(s.getOutputSimpleRouteJson(),null,2)+'\n');console.log(JSON.stringify(result))
