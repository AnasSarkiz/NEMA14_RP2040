import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {bindEndpoints}=await import('./bind-endpoints');const {default:Candidate}=await import('./candidate');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Candidate({copper:!process.argv.includes('--no-copper')}));await c.renderUntilSettled();if(!process.argv.includes('--no-copper'))bindEndpoints(c);writeFileSync(process.argv[2],JSON.stringify(c.getCircuitJson(),null,2)+'\n')
