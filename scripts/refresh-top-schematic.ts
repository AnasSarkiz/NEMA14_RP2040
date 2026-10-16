import {prepareSchematic} from './prepare-schematic'
import {readFileSync,writeFileSync} from 'node:fs'
const raw=JSON.parse(readFileSync('artifacts/top-assembly/raw-source.circuit.json','utf8'));const json=prepareSchematic(raw);writeFileSync('artifacts/final-source.circuit.json',JSON.stringify(json,null,2)+'\n');console.log('Refreshed functional sheets',json.filter((e:any)=>e.type==='schematic_sheet').length)
