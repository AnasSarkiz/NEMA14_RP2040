/** Routing-disabled native authoring control; no board acceptance is implied. */
import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {mkdirSync,writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Candidate}=await import('./escape')
const out=process.argv[2]??'.config/reachability/authored.circuit.json'
const route=process.argv.includes('--route')
mkdirSync(out.slice(0,out.lastIndexOf('/')),{recursive:true})
const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}})
c.pcbRoutingDisabled=!route;c.on('autorouting:start',(e:any)=>writeFileSync(out+'.routing-input.json',JSON.stringify(e,null,2)+'\n'));c.add(Candidate({routingDisabled:!route}));const started=performance.now();await c.renderUntilSettled();writeFileSync(out+'.receipt.json',JSON.stringify({routing_enabled:route,schematic_disabled:true,parts_engine_disabled:true,elapsed_ms:performance.now()-started},null,2)+'\n')
writeFileSync(out,JSON.stringify(c.getCircuitJson(),null,2)+'\n')
