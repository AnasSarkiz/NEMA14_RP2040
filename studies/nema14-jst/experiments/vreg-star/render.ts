import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:paths}=await import('../original-process/paths.json');const {default:path}=await import('./path.json');const {bindEndpoints}=await import('../original-process/bind-endpoints');const {default:Candidate}=await import('./candidate');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Candidate({copper:!process.argv.includes('--no-copper'),vreg:!process.argv.includes('--no-vreg')}));await c.renderUntilSettled();if(!process.argv.includes('--no-copper'))bindEndpoints(c,process.argv.includes('--no-vreg')?paths:[...paths,path]);writeFileSync(process.argv[2],JSON.stringify(c.getCircuitJson(),null,2)+'\n')
