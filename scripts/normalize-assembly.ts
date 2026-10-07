import type { AnyCircuitElement } from "circuit-json"

// Through-hole joints are hand soldered from the top. Do not put paste over
// their drill openings or generate a bottom stencil for a top-assembly board.
export function normalizeAssembly(json: AnyCircuitElement[]) {
  const holes = json.filter(e => e.type === "pcb_plated_hole")
  return json.filter(e => {
    if (e.type !== "pcb_solder_paste") return true
    if (e.layer !== "top") return false
    if (!("x" in e)) return true
    const { x, y } = e
    return !holes.some(h => Math.hypot(h.x-x,h.y-y)<0.001)
  })
}
