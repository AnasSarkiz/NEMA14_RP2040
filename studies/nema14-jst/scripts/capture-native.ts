import {mkdirSync, copyFileSync} from "node:fs"
mkdirSync("artifacts",{recursive:true})
copyFileSync("dist/controller/circuit.json","artifacts/final-source.circuit.json")
