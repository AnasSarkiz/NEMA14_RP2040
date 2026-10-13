import type { AnyCircuitElement } from "circuit-json"

// Through-hole joints are hand soldered from the top. Do not put paste over
// their drill openings. Preserve native SMT paste on both assembly sides.
export function normalizeAssembly(json: AnyCircuitElement[]) {
  const sources=new Map(json.filter(e=>e.type==='source_component').map(e=>[e.source_component_id,e]))
  const bareIds=new Set(json.filter((e):e is Extract<AnyCircuitElement,{type:'pcb_component'}>=>e.type==='pcb_component'&&sources.get(e.source_component_id)?.ftype==='simple_test_point').map(e=>e.pcb_component_id))
  const holes = json.filter(e => e.type === "pcb_plated_hole")
  return json.filter(e => {
    if (e.type !== "pcb_solder_paste") return true
    if(e.layer!=="top" || bareIds.has(e.pcb_component_id??""))return false
    if (!("x" in e)) return true
    const { x, y } = e
    return !holes.some(h => Math.hypot(h.x-x,h.y-y)<0.001)
  })
}
