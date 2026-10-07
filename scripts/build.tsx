import React from "react"
import { classifySource } from "./classify-source"
import { prepareSchematic } from "./prepare-schematic"
import { Circuit } from "tscircuit"
import { convertCircuitJsonToPcbSvg, convertCircuitJsonToSchematicSvg } from "circuit-to-svg"
import { mkdirSync, writeFileSync } from "node:fs"
import Nema14Controller from "../index.circuit"
import { normalizeAssembly } from "./normalize-assembly"
const circuit = new Circuit()
circuit.add(<Nema14Controller routingDisabled={process.argv.includes("--unrouted")} />)
console.log('Rendering NEMA14 RP2040 with tscircuit local autorouter…')
await circuit.renderUntilSettled()
const json = prepareSchematic(classifySource(normalizeAssembly(circuit.getCircuitJson())))
mkdirSync('artifacts', {recursive:true})
writeFileSync(process.argv.includes('--unrouted') ? 'artifacts/final-source.circuit.json' : 'artifacts/autorouted.circuit.json', JSON.stringify(json,null,2)+'\n')
if(!process.argv.includes('--unrouted')) {
writeFileSync('artifacts/autorouted-top.svg', convertCircuitJsonToPcbSvg(json,{layer:'top'}))
writeFileSync('artifacts/autorouted-bottom.svg', convertCircuitJsonToPcbSvg(json,{layer:'bottom'}))
}
writeFileSync('artifacts/schematic.svg', convertCircuitJsonToSchematicSvg(json))
console.log(JSON.stringify({elements:json.length,traces:json.filter(e=>e.type==='pcb_trace').length,errors:json.filter(e=>e.type.endsWith('_error')).map(e=>({type:e.type,message:(e as any).message}))},null,2))

if(json.some(e=>e.type.endsWith('_error'))) process.exitCode=1
