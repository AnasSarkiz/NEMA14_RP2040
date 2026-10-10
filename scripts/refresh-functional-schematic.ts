import {readFileSync,writeFileSync,unlinkSync,readdirSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
import {createHash} from 'node:crypto'
import {prepareSchematic} from './prepare-schematic'
const proof:any={schema:'functional-schematic-invariance-v1',compared_git_revision:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),boards:[]}
for(const file of ['artifacts/board.circuit.json','artifacts/final-source.circuit.json']){
 const current:any[]=JSON.parse(readFileSync(file,'utf8'));const next=prepareSchematic(current)
 const baseline=execFileSync('git',['show',`HEAD:${file}`],{maxBuffer:100_000_000});const previous:any[]=JSON.parse(baseline.toString())
 const nonSchematic=(j:any[])=>j.filter(e=>!e.type.startsWith('schematic_'))
 if(JSON.stringify(nonSchematic(previous))!==JSON.stringify(nonSchematic(next)))throw new Error('Non-schematic records changed')
 const pins=(j:any[])=>j.filter(e=>e.type==='schematic_port').map(e=>[e.schematic_port_id,e.source_port_id,e.pin_number]).sort()
 if(JSON.stringify(pins(previous))!==JSON.stringify(pins(next)))throw new Error('Symbol pin identity changed')
 if(JSON.stringify(prepareSchematic(next))!==JSON.stringify(next))throw new Error('Functional preparation is not idempotent')
 proof.boards.push({file,before_sha256:createHash('sha256').update(baseline).digest('hex'),after_sha256:createHash('sha256').update(JSON.stringify(next,null,2)+'\n').digest('hex'),non_schematic_records_byte_equivalent:true,schematic_pin_identities_preserved:true,old_sheets:previous.filter(e=>e.type==='schematic_sheet').length,new_sheets:next.filter(e=>e.type==='schematic_sheet').map(e=>e.name)})
 writeFileSync(file,JSON.stringify(next,null,2)+'\n')
}
writeFileSync('index.circuit.json',readFileSync('artifacts/board.circuit.json'))
// Retire generated pages/screenshots that no longer exist in the delivered sheet set.
for(const f of readdirSync('artifacts'))if(/^schematic-a4-page-\d+\.(svg|png)$/.test(f))unlinkSync('artifacts/'+f)
const sheets=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8')).filter((e:any)=>e.type==='schematic_sheet')
for(const f of readdirSync('artifacts/validation/service-schematic-ui'))if(/^page-\d+\.png$/.test(f)&&Number(f.slice(5,7))>sheets.length)unlinkSync('artifacts/validation/service-schematic-ui/'+f)
writeFileSync('artifacts/validation/functional-schematic-invariance.json',JSON.stringify(proof,null,2)+'\n')
console.log(proof)
