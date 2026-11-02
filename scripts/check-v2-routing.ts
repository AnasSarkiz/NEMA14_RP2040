// Preserve every native error/warning; this check never qualifies manufacturing.
import { createHash } from "node:crypto"
import { readFileSync, writeFileSync } from "node:fs"
import { runAllChecks, checkViasInPads } from "@tscircuit/checks"

const source=process.argv[2]??"artifacts/v2/routing/freerouted.circuit.json"
const output=process.argv[3]??"artifacts/v2/routing/native-drc.json"
const bytes=readFileSync(source)
const json=JSON.parse(bytes.toString())
const checks=await runAllChecks(json)
const sites=JSON.parse(readFileSync("artifacts/v2/routing/thermal-via-sites.json","utf8")).sites
const allowed=new Set<string>()
const ground=json.find((e:any)=>e.type==="source_net"&&e.name==="GND")
for(const reference of ["U_MCU","U_PD","U_DRV"]){
  const site=sites.find((s:any)=>s.reference===reference)
  const source=json.find((e:any)=>e.type==="source_component"&&e.name===reference)
  const component=json.find((e:any)=>e.type==="pcb_component"&&e.source_component_id===source?.source_component_id)
  const via=json.find((e:any)=>e.type==="pcb_via"&&e.pcb_via_id===site?.pcb_via_id)
  const pad=json.find((e:any)=>e.type==="pcb_smtpad"&&e.pcb_smtpad_id===site?.pcb_pad_id&&e.pcb_component_id===component?.pcb_component_id)
  const port=json.find((e:any)=>e.type==="pcb_port"&&e.pcb_port_id===pad?.pcb_port_id)
  const sourcePort=json.find((e:any)=>e.type==="source_port"&&e.source_port_id===port?.source_port_id)
  const quarterTurn=Math.abs((pad?.ccw_rotation??0)%180-90)<.01
  const width=quarterTurn?pad?.height:pad?.width,height=quarterTurn?pad?.width:pad?.height
  if(!via||!pad||via.source_net_id!==ground.source_net_id||sourcePort?.subcircuit_connectivity_map_key!==ground.subcircuit_connectivity_map_key||
    Math.hypot(via.x-site.x,via.y-site.y)>1e-6||via.outer_diameter!==.5||via.hole_diameter!==.3||
    Math.abs(via.x-pad.x)+.30>width/2||Math.abs(via.y-pad.y)+.30>height/2)
    throw new Error("Invalid grounded exposed-pad thermal via: "+reference)
  allowed.add(via.pcb_via_id)
}
// Apply the via-in-pad rule to every other via; the exception is restricted
// to one validated grounded barrel inside each of these three exposed pads.
checks.push(...checkViasInPads(json.filter((e:any)=>!(e.type==="pcb_via"&&allowed.has(e.pcb_via_id)))
  .map((e:any)=>e.type==="pcb_board"?{...e,is_via_in_pad_allowed:false}:e)))
const errors=[...json.filter((e:any)=>e.type.endsWith("_error")),...checks.filter((e:any)=>e.type.endsWith("_error"))]
const unique=[...new Map(errors.map((e:any)=>[JSON.stringify(e),e])).values()]
const report={passed:unique.length===0,source_sha256:createHash("sha256").update(bytes).digest("hex"),
  errors:unique,warnings:checks.filter((e:any)=>e.type.endsWith("_warning")),fabrication_ready:false}
writeFileSync(output,JSON.stringify(report,null,2)+"\n")
console.log(JSON.stringify({...report,errors:report.errors.length,warnings:report.warnings.length}))
if(!report.passed)process.exitCode=1
