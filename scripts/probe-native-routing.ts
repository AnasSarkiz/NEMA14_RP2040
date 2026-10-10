import {getSimpleRouteJsonFromCircuitJson} from '@tscircuit/core'
import {readFileSync,writeFileSync} from 'node:fs'
const j=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
const {simpleRouteJson:input}=getSimpleRouteJsonFromCircuitJson({circuitJson:j,minTraceWidth:.16,minTraceToPadEdgeClearance:.15,minViaHoleDiameter:.25,minViaPadDiameter:.5,subcircuit_id:'subcircuit_source_group_0'})
writeFileSync('artifacts/validation/independent-native-input.json',JSON.stringify(input,null,2))
console.log('Connections:',input.connections.length,'existing traces:',input.traces?.length,'obstacles:',input.obstacles.length)
console.log(input.connections.slice(0,2))
