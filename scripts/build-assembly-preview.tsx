import React from "react"
import { Circuit } from "tscircuit"
import Preview from "../assembly-preview.circuit"
import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"

const nativePath = "artifacts/board.circuit.json"
const nativeBytes = readFileSync(nativePath)
const native = JSON.parse(nativeBytes.toString())
const circuit = new Circuit()
circuit.schematicDisabled = true
circuit.add(<Preview />)
await circuit.renderUntilSettled()
const fresh = circuit.getCircuitJson() as any[]
const errors = fresh.filter(e => e.type.endsWith("_error"))
if (errors.length) throw new Error(JSON.stringify(errors))
const nativeSources = new Map(native.filter((e:any) => e.type === "source_component").map((e:any) => [e.name, e]))
const freshSources = fresh.filter(e => e.type === "source_component")
const extraSources = freshSources.filter(e => !nativeSources.has(e.name))
const extraIds = new Set(extraSources.map(e => e.source_component_id))
const idMap = new Map(freshSources.map(e => [e.source_component_id,
  nativeSources.has(e.name) ? (nativeSources.get(e.name) as any).source_component_id : `assembly_${e.source_component_id}`]))
const nativeByName = (type:string, j:any[]) => new Map(j.filter(e => e.type === type).map(e => {
  const s=j.find(q => q.type === "source_component" && q.source_component_id === e.source_component_id)
  return [s?.name,e]
}))
// All displayed electronic component CAD poses must come from reviewed copper.
const nativeCad=nativeByName("cad_component",native), freshCad=nativeByName("cad_component",fresh)
for (const [name,n] of nativeCad) {
  const f=freshCad.get(name)
  if (!f || JSON.stringify(n.position)!==JSON.stringify(f.position) || JSON.stringify(n.rotation)!==JSON.stringify(f.rotation))
    throw new Error(`Source/qualified PCB pose mismatch: ${name}`)
}
function remap(e:any) {
  const r=structuredClone(e)
  for(const field of ["source_component_id","from_source_component_id","to_source_component_id"])
    if(r[field]) r[field]=idMap.get(r[field]) ?? r[field]
  if(r.cad_component_id) r.cad_component_id=`assembly_${r.cad_component_id}`
  if(r.cad_cable_id) r.cad_cable_id=`assembly_${r.cad_cable_id}`
  // Mechanical parts are outside the electrical subcircuit.
  delete r.subcircuit_id
  return r
}
const extraCad=fresh.filter(e => e.type === "cad_component" && extraIds.has(e.source_component_id)).map(remap)
const cables=fresh.filter(e => e.type === "cad_cable").map(remap)
if(extraCad.length!==9 || cables.length!==1) throw new Error("Incomplete motor/hardware/cable assembly")
const output=[...native,...extraSources.map(remap),...extraCad,...cables]
if(JSON.stringify(output.slice(0,native.length))!==JSON.stringify(native)) throw new Error("Qualified board records changed")
writeFileSync("artifacts/top-assembly/assembly-preview.circuit.json",JSON.stringify(output,null,2)+"\n")
writeFileSync("assembly.circuit.json",JSON.stringify(output,null,2)+"\n")
const proof={passed:true,board_sha256:createHash("sha256").update(nativeBytes).digest("hex"),
  qualified_board_records_preserved:true,electronic_CAD_poses_match:true,source_render_errors:errors,
  added_mechanical_components:extraSources.map(e=>e.name),motor_to_PCB_surface_gap_mm:6,
  screw_head_mm:{diameter:4,height:3},screw_shaft_mm:{diameter:3,length:6},
  spacer_mm:{outer_diameter:5,bore_diameter:3.2,length:6},
  actual_motor_rear_retention_verified:false,physical_assembly_tested:false,
  cable_obstacle_avoidance_provided_by_tscircuit:false,
  documentation:["https://docs.tscircuit.com/elements/assembly-motor","https://docs.tscircuit.com/elements/assembly-cable","https://docs.tscircuit.com/guides/tscircuit-essentials/mounting-3d-models"]}
writeFileSync("artifacts/top-assembly/assembly-build-verification.json",JSON.stringify(proof,null,2)+"\n")
console.log(JSON.stringify(proof,null,2))
