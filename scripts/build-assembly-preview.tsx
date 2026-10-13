import React from "react"
import {Circuit} from "tscircuit"
import Preview from "../assembly-preview.circuit"
import {writeFileSync} from "node:fs"
const circuit=new Circuit();circuit.add(<Preview/>);await circuit.renderUntilSettled();const json=circuit.getCircuitJson();writeFileSync("artifacts/top-assembly/assembly-preview.circuit.json",JSON.stringify(json,null,2)+"\n");console.log(JSON.stringify({motor:json.filter((e:any)=>e.type==="source_component"&&e.ftype==="motor"),cables:json.filter((e:any)=>e.type==="cad_cable"),errors:json.filter((e:any)=>e.type.endsWith("_error"))},null,2));
