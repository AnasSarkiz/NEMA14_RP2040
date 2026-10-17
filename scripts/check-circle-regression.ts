import { checkEachPcbTraceNonOverlapping } from "@tscircuit/checks"
import { writeFileSync } from "node:fs"

const board = {type:"pcb_board",pcb_board_id:"fixture-board",width:35,height:35,center:{x:0,y:0},num_layers:4,min_trace_to_pad_edge_clearance:0.15}
function check(shape:string, y:number, layer="top") {
  const keepout = {type:"pcb_keepout",pcb_keepout_id:"fixture-keepout",shape,center:{x:0,y:0},radius:2.2,width:4.4,height:4.4,layers:["top"]}
  const trace = {type:"pcb_trace",pcb_trace_id:"fixture-trace",route:[{route_type:"wire",x:1.9,y,layer,width:.16},{route_type:"wire",x:2.1,y,layer,width:.16}]}
  return checkEachPcbTraceNonOverlapping([board,keepout,trace] as any).length
}
const results = {
  circleCornerClear:check("circle",1.9)===0,
  circleIntrusionRejected:check("circle",1)===1,
  circleClearanceViolationRejected:check("circle",1.3)===1,
  rectangleCornerStillRejected:check("rect",1.9)===1,
  otherLayerUnaffected:check("circle",1,"bottom")===0,
}
if(Object.values(results).some(v=>!v)) throw new Error(JSON.stringify(results))
writeFileSync("artifacts/upright-revision/circle-checker-regression.json",JSON.stringify({passed:true,results},null,2)+"\n")
console.log("Circular keepout regression checks PASS",results)
