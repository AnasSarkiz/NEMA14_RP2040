import {readFileSync,writeFileSync} from 'node:fs'
import {prepareSchematic} from './prepare-schematic'
const path='artifacts/final-source.circuit.json';const old=JSON.parse(readFileSync(path,'utf8'));const updated=prepareSchematic(old)
if(JSON.stringify(old.filter((e:any)=>!e.type.startsWith('schematic_')))!==JSON.stringify(updated.filter((e:any)=>!e.type.startsWith('schematic_'))))throw Error('Schematic generation modified non-schematic records')
writeFileSync(path,JSON.stringify(updated,null,2)+'\n');console.log('Rebuilt',updated.filter((e:any)=>e.type==='schematic_sheet').length,'functional sheets')
