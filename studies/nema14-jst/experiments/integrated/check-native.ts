import * as checks from '@tscircuit/checks'
import {readFileSync,writeFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
const [input,out]=process.argv.slice(2);const j=JSON.parse(readFileSync(input,'utf8'));const names=['checkPadPadClearance','checkPadTraceClearance','checkEachPcbTraceNonOverlapping','checkViaPadClearance','checkViaTraceClearance','checkViasInPads','checkTracesAreContiguous','checkSourceTracesMatchPcbTraceThickness','checkPcbCopperOverKeepout','checkCopperToBoardEdgeClearance','checkSameNetViaSpacing','checkDifferentNetViaSpacing'];const r:any={};for(const n of names){try{const e=await (checks as any)[n](j);r[n]={count:e.length,findings:e}}catch(e){r[n]={exception:String(e)}}}writeFileSync(out,JSON.stringify(r,null,2)+'\n');console.log(Object.fromEntries(Object.entries(r).map(([k,v]:any)=>[k,v.count??v.exception])))

writeFileSync(out+'.meta.json',JSON.stringify({checker_version:JSON.parse(readFileSync('node_modules/@tscircuit/checks/package.json','utf8')).version,input_sha256:createHash('sha256').update(readFileSync(input)).digest('hex')},null,2)+'\n')

if(process.argv.includes('--all')){const all=await checks.runAllRoutingChecks(j);writeFileSync(out+'.all-routing.json',JSON.stringify({count:all.length,by_type:all.reduce((r:any,e:any)=>{r[e.type]=(r[e.type]??0)+1;return r},{}),findings:all},null,2)+'\n')}
