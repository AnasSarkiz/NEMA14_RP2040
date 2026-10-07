import { readFileSync, writeFileSync } from "node:fs"
import { convertCircuitJsonToPcbSvg, convertCircuitJsonToSchematicSvg } from "circuit-to-svg"
import { Resvg } from "@resvg/resvg-js"
const json=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
for (const layer of ['top','inner1','inner2','bottom'] as const) {
 const svg=convertCircuitJsonToPcbSvg(json,{layer})
 writeFileSync(`artifacts/pcb-${layer}.svg`,svg)
 writeFileSync(`artifacts/pcb-${layer}.png`,new Resvg(svg,{fitTo:{mode:'width',value:1500}}).render().asPng())
}
const sheets=json.filter((e:any)=>e.type==='schematic_sheet')
for(const [index,sheet] of sheets.entries()) {
 const schematicSvg=convertCircuitJsonToSchematicSvg(json,{width:2970,height:2100,schematicSheetId:sheet.schematic_sheet_id})
  .replace("<svg ", '<svg viewBox="0 0 2970 2100" ')
  .replace(/width="2970"/, 'width="297mm"').replace(/height="2100"/, 'height="210mm"')
 const suffix=String(index+1).padStart(2,'0')
 writeFileSync(`artifacts/schematic-a4-page-${suffix}.svg`,schematicSvg)
 const png=new Resvg(schematicSvg,{fitTo:{mode:'width',value:2970}}).render().asPng()
 writeFileSync(`artifacts/schematic-a4-page-${suffix}.png`,png)
 if(index===0) {
  writeFileSync('artifacts/schematic.svg',schematicSvg)
  writeFileSync('artifacts/schematic-a4.png',png)
 }
}
