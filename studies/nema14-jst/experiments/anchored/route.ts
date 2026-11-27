import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {mkdirSync,writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Native}=await import('./native-entry');const net=process.argv[2]??'CP1';const scope=(process.argv[3]??'coupon') as 'coupon'|'guarded'|'board';const smallStar=process.argv.includes('--small-star');const out=process.argv.find(v=>v.startsWith('--out='))?.slice(6)??'artifacts/iteration-6/'+scope+'-'+net+(smallStar?'-small-star':'');mkdirSync(out,{recursive:true});const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.add(Native({net,scope,smallStar,out}));await c.renderUntilSettled();writeFileSync(out+'/native.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n')
