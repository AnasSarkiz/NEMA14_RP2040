/** Rebuild the functional drawing around the saved, locally routed board. */
import { readFileSync, writeFileSync } from 'node:fs'
import { prepareSchematic } from './prepare-schematic'
const path='artifacts/board.circuit.json'
const before=JSON.parse(readFileSync(path,'utf8'))
const after=prepareSchematic(before)
const electrical=(records:any[])=>records.filter(e=>!e.type.startsWith('schematic_'))
if(JSON.stringify(electrical(before))!==JSON.stringify(electrical(after)))throw Error('Drawing generation changed electrical or PCB records')
writeFileSync(path,JSON.stringify(after,null,2)+'\n')
console.log('Regenerated six functional sheets; electrical and PCB records retained.')
