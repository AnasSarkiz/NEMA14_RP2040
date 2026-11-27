import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
import Fixture from './via-multi-fixture'
const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Fixture());await c.renderUntilSettled();writeFileSync('artifacts/iteration-5/via-multi-fixture.circuit.json',JSON.stringify(c.getCircuitJson(),null,2)+'\n');console.log(c.getCircuitJson().filter((e:any)=>e.type==='pcb_trace'||e.type==='pcb_via'||e.type.endsWith('_error')))
