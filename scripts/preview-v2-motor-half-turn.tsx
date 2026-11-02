// Isolated rotation trial: never rewrites the active placement or main previews.
import React from "react"
import { Circuit } from "tscircuit"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { convertCircuitJsonToPcbSvg } from "circuit-to-svg"
import placements from "../src/supplier-placement.json"
import { classifySource } from "./classify-source"
import { normalizeMetadata } from "./normalize-metadata"
import { prepareSchematic } from "./prepare-schematic"

const directory="artifacts/v2/rotation-study"
const study=JSON.parse(readFileSync(`${directory}/rotation-screen.json`,"utf8"))
const trial=study.half_turn_same_occupied_area
Object.assign(placements.J_MOTOR,{
  pcbX:trial.pcbX,pcbY:trial.pcbY,pcbRotation:trial.pcbRotation,
})
const {default:Board}=await import("../src/board")
const circuit=new Circuit()
circuit.pcbRoutingDisabled=true
circuit._featureMspSchematicTraceRouting=false
circuit.add(<Board routingDisabled />)
await circuit.renderUntilSettled()
const json=prepareSchematic(normalizeMetadata(classifySource(circuit.getCircuitJson())))
mkdirSync(directory,{recursive:true})
writeFileSync(`${directory}/half-turn.circuit.json`,JSON.stringify(json,null,2)+"\n")
writeFileSync(`${directory}/half-turn-pcb.svg`,convertCircuitJsonToPcbSvg(json,{layer:"top"}))
const errors=json.filter(e=>e.type.endsWith("_error"))
console.log(JSON.stringify({trial:"180-degree terminal only",elements:json.length,errors,main_layout_changed:false}))
if(errors.length)process.exitCode=1
