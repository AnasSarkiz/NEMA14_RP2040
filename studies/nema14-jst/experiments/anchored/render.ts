import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Fixture}=await import('./fixture');const scope=(process.argv.find(v=>v.startsWith('--scope='))?.split('=')[1]??'coupon') as 'coupon'|'guarded'|'board';const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Fixture({scope,routingDisabled:true,copper:!process.argv.includes('--no-copper'),smallStar:process.argv.includes('--small-star'),forceSingular:process.argv.includes('--force-singular'),allPlural:process.argv.includes('--all-plural'),anchorShift:Number(process.argv.find(v=>v.startsWith('--shift-shunt='))?.split('=')[1]??0)}));await c.renderUntilSettled();writeFileSync(process.argv[2],JSON.stringify(c.getCircuitJson(),null,2)+'\n')
