import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {bindDriverEndpoints}=await import('../anchored/bind-endpoints');const {default:Candidate}=await import('./candidate');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Candidate({copper:!process.argv.includes('--no-copper'),chargePump:!process.argv.includes('--without-charge-pump'),process:process.argv.includes('--small-hole-screen')?'small-hole-screen':'locked'}));await c.renderUntilSettled();if(!process.argv.includes('--no-copper'))bindDriverEndpoints(c);writeFileSync(process.argv[2],JSON.stringify(c.getCircuitJson(),null,2)+'\n')
