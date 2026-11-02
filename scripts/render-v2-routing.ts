import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { Resvg } from "@resvg/resvg-js"
import { convertCircuitJsonToPcbSvg } from "circuit-to-svg"

const source=process.argv[2]??"artifacts/v2/routing/freerouted.circuit.json"
const bytes=readFileSync(source)
const json=JSON.parse(bytes.toString())
const hash=createHash("sha256").update(bytes).digest("hex")
for(const layer of ["top","inner1","inner2","bottom"] as const){
  const svg=convertCircuitJsonToPcbSvg(json,{layer})
    .replace("<svg ",`<svg data-source-sha256="${hash}" data-status="routing-draft-not-for-ordering" `)
    .replace(/[ \t]+$/gm,"")
  writeFileSync(`artifacts/v2/routing/${layer}.svg`,svg)
  writeFileSync(`artifacts/v2/routing/${layer}.png`,new Resvg(svg,{fitTo:{mode:"width",value:1400}}).render().asPng())
}
console.log(JSON.stringify({source_sha256:hash,layers:4,stage:"routing draft, not for ordering"}))
