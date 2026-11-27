import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Candidate}=await import('./candidate');const {default:old}=await import('../original-process/paths.json');const {default:vreg}=await import('../vreg-star/path.json');const {default:path}=await import('./path.json');const {bindEndpoints}=await import('../original-process/bind-endpoints');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Candidate());await c.renderUntilSettled();bindEndpoints(c,[...old,vreg,path]);writeFileSync(process.argv[2]||'artifacts/iteration-14/candidate.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n')
