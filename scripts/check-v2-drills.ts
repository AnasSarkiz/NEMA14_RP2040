import { readFileSync, writeFileSync } from "node:fs"
import { convertCircuitJsonToExcellonDrillCommands, stringifyExcellonDrill } from "circuit-json-to-gerber"

// Diagnostic NPTH conversion only. This is not a manufacturing export.
const json=JSON.parse(readFileSync("artifacts/v2/source.circuit.json","utf8"))
const commands=convertCircuitJsonToExcellonDrillCommands({circuitJson:json,is_plated:false})
const slots=commands.filter(c=>c.command_code==="G85")
if(slots.length!==2)throw Error(`Expected one NPTH slot per USB connector, got ${slots.length}`)
const diameter=0.7099808,length=1.5099792
for(const slot of slots){
  if(Math.abs(slot.width-diameter)>1e-6)throw Error("USB slot cutter diameter changed")
  const index=commands.indexOf(slot),start=commands[index-1] as any
  if(start.command_code!=="drill_at")throw Error("USB slot lacks its start point")
  if(Math.abs(Math.hypot(slot.x-start.x,slot.y-start.y)+diameter-length)>1e-6)throw Error("USB routed slot length changed")
}
const report={purpose:"Diagnostic NPTH conversion only; not order files",usb_slot_count:slots.length,
  slot_overall_mm:[length,diameter],uses_excellon_routed_slots:true}
writeFileSync("artifacts/v2/usb-slot-export-check.json",JSON.stringify(report,null,2)+"\n")
writeFileSync("artifacts/v2/diagnostic-npth-not-for-order.drl",stringifyExcellonDrill(commands))
console.log(JSON.stringify(report))
