import {readFileSync,mkdirSync,writeFileSync} from "node:fs"
import {convertCircuitJsonToPcbSvg} from "circuit-to-svg"
const board=JSON.parse(readFileSync("artifacts/final-source.circuit.json","utf8"))
mkdirSync("review",{recursive:true})
for(const layer of ["top","bottom"] as const) writeFileSync(`review/${layer}.svg`,convertCircuitJsonToPcbSvg(board,{layer}))
