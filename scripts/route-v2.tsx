// V2 routing candidates are isolated from the placement seed and V1 order files.
import React from "react"
import { Circuit } from "tscircuit"
import { createHash } from "node:crypto"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import Board from "../src/board"
import { classifySource } from "./classify-source"
import { normalizeMetadata } from "./normalize-metadata"
import { prepareSchematic } from "./prepare-schematic"

const directory="artifacts/v2/routing"
mkdirSync(directory,{recursive:true})
const baselineSha=createHash("sha256").update(readFileSync("artifacts/v2/source.circuit.json")).digest("hex")
const circuit=new Circuit()
circuit._featureMspSchematicTraceRouting=false
circuit.add(<Board routingDisabled={false} />)
const started=Date.now()
const progress=setInterval(()=>{
  const json=circuit.getCircuitJson()
  const state={stage:"routing candidate, not for ordering",elapsed_seconds:Math.round((Date.now()-started)/1000),
    placement_source_sha256:baselineSha,records:json.length,
    traces:json.filter(e=>e.type==="pcb_trace").length,
    vias:json.filter(e=>e.type==="pcb_via").length}
  writeFileSync(`${directory}/native-progress.json`,JSON.stringify(state,null,2)+"\n")
  console.log(JSON.stringify(state))
},10000)
let failure:unknown
try { await circuit.renderUntilSettled() } catch(error) { failure=error }
finally { clearInterval(progress) }
const json=prepareSchematic(normalizeMetadata(classifySource(circuit.getCircuitJson())))
const bytes=JSON.stringify(json,null,2)+"\n"
writeFileSync(`${directory}/native-candidate.circuit.json`,bytes)
const report={stage:"routing candidate, not for ordering",placement_source_sha256:baselineSha,
  candidate_sha256:createHash("sha256").update(bytes).digest("hex"),
  elapsed_seconds:Math.round((Date.now()-started)/1000),
  traces:json.filter(e=>e.type==="pcb_trace").length,vias:json.filter(e=>e.type==="pcb_via").length,
  native_errors:json.filter(e=>e.type.endsWith("_error")),
  failure:failure?String(failure):null, fabrication_ready:false}
writeFileSync(`${directory}/native-routing-review.json`,JSON.stringify(report,null,2)+"\n")
console.log(JSON.stringify({...report,native_errors:report.native_errors.length,
  first_errors:report.native_errors.slice(0,3)}))
if(failure||report.native_errors.length)process.exitCode=1
