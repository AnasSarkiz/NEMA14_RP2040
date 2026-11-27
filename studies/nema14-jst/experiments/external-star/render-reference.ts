import {Circuit} from '@tscircuit/core'
import {writeFileSync} from 'node:fs'
import Reference from './reference'
const c=new Circuit({platform:{partsEngineDisabled:true,schematicDisabled:true}});c.pcbRoutingDisabled=true;c.add(Reference());await c.renderUntilSettled();writeFileSync(process.argv[2],JSON.stringify(c.getCircuitJson(),null,2)+'\n')
