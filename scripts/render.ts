import { readFileSync, writeFileSync } from "node:fs"
import { convertCircuitJsonToPcbSvg, convertCircuitJsonToSchematicSvg } from "circuit-to-svg"
import { Resvg } from "@resvg/resvg-js"
const json=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
for (const layer of ['top','bottom'] as const) {
 const svg=convertCircuitJsonToPcbSvg(json,{layer})
 writeFileSync(`artifacts/pcb-${layer}.svg`,svg)
 writeFileSync(`artifacts/pcb-${layer}.png`,new Resvg(svg,{fitTo:{mode:'width',value:1500}}).render().asPng())
}
writeFileSync('artifacts/schematic.svg',convertCircuitJsonToSchematicSvg(json))
