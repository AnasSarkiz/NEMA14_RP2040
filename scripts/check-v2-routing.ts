// Preserve every native error/warning; this check never qualifies manufacturing.
import { createHash } from "node:crypto"
import { readFileSync, writeFileSync } from "node:fs"
import { runAllChecks, checkViasInPads } from "@tscircuit/checks"

const source=process.argv[2]??"artifacts/v2/routing/freerouted.circuit.json"
const output=process.argv[3]??"artifacts/v2/routing/native-drc.json"
const bytes=readFileSync(source)
const json=JSON.parse(bytes.toString())
const checks=await runAllChecks(json)
checks.push(...checkViasInPads(json.map((e:any)=>e.type==="pcb_board"?{...e,is_via_in_pad_allowed:false}:e)))
const errors=[...json.filter((e:any)=>e.type.endsWith("_error")),...checks.filter((e:any)=>e.type.endsWith("_error"))]
const unique=[...new Map(errors.map((e:any)=>[JSON.stringify(e),e])).values()]
const report={passed:unique.length===0,source_sha256:createHash("sha256").update(bytes).digest("hex"),
  errors:unique,warnings:checks.filter((e:any)=>e.type.endsWith("_warning")),fabrication_ready:false}
writeFileSync(output,JSON.stringify(report,null,2)+"\n")
console.log(JSON.stringify({...report,errors:report.errors.length,warnings:report.warnings.length}))
if(!report.passed)process.exitCode=1
