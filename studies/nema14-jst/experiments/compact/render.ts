import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Candidate}=await import('./candidate');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Candidate({routingDisabled:true,scope:process.argv.includes('--scope'),copper:!process.argv.includes('--no-copper')}));await c.renderUntilSettled();writeFileSync(process.argv[2]??'artifacts/iteration-5/placement.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n')
