import {plugin} from 'bun'
import {Circuit} from '@tscircuit/core'
import {writeFileSync,mkdirSync} from 'node:fs'
plugin({name:'local-cad',setup(b){b.onLoad({filter:/\.(obj|step)$/},a=>({contents:'export default '+JSON.stringify(a.path),loader:'js'}))}})
const {default:Driver}=await import('./native-driver');const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});mkdirSync('artifacts/iteration-5/core-driver',{recursive:true});c.add(Driver());await c.renderUntilSettled();writeFileSync('artifacts/iteration-5/core-driver/native.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n')
