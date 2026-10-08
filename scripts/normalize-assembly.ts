import type { AnyCircuitElement } from "circuit-json"

// Assembly process: top SMT reflow; USB shield slots and motor wires are
// hand soldered afterward. Bare debug/boot interfaces are not fitted parts.
// Native copper, mask and drilled land patterns are never altered here.
export function normalizeAssembly(json: AnyCircuitElement[]) {
  const holes = json.filter(e => e.type === "pcb_plated_hole")
  const source = new Map(json.filter(e => e.type === "source_component").map(e => [e.source_component_id, e.name]))
  const components = new Map(json.filter(e => e.type === "pcb_component").map(e => [e.pcb_component_id, source.get(e.source_component_id)]))
  const bare = new Set(["J_MOTOR", "J_DEBUG", "J_BOOT"])
  const pads = new Map(json.filter(e => e.type === "pcb_smtpad").map(e => [e.pcb_smtpad_id, e]))
  const panes: AnyCircuitElement[] = []
  const emitted = new Set<string>()
  const filtered = json.filter(e => {
    if (e.type !== "pcb_solder_paste") return true
    if (e.layer !== "top" || bare.has(components.get(e.pcb_component_id ?? "") ?? "")) return false
    if (!("x" in e)) return true
    if (holes.some(h => Math.hypot(h.x-e.x,h.y-e.y)<0.001)) return false
    const p = pads.get(e.pcb_smtpad_id ?? "")
    if (p?.shape === "rect" && p.width > 2 && p.height > 2 && ["U_PD", "U_MCU", "U_DRV"].includes(components.get(p.pcb_component_id ?? "") ?? "")) {
      if (!emitted.has(p.pcb_smtpad_id)) {
        const w = Math.sqrt(0.60)*p.width/2, h = Math.sqrt(0.60)*p.height/2, gap=0.2
        for (const ix of [-1,1]) for (const iy of [-1,1]) panes.push({...e, shape:"rect", pcb_solder_paste_id:`${e.pcb_solder_paste_id}_pane_${ix}_${iy}`, width:w, height:h, x:p.x+ix*(w+gap)/2, y:p.y+iy*(h+gap)/2})
        emitted.add(p.pcb_smtpad_id)
      }
      return false
    }
    // Fine-pitch QFN leads: 100 um stencil candidate, 90% rectangular
    // native-pad dimensions. Rounded driver leads use an inscribed rectangle,
    // so paste cannot protrude past the copper's rounded ends.
    if (e.shape === "rect" && p && ["U_MCU", "U_DRV"].includes(components.get(p.pcb_component_id ?? "") ?? "")) {
      if (p.shape === "rect" && Math.min(p.width,p.height) <= 0.35) {
        panes.push({...e, width:p.width*0.9, height:p.height*0.9, x:p.x, y:p.y})
        return false
      }
      if (p.shape === "pill" || p.shape === "rotated_pill") {
        const short=Math.min(p.width,p.height), long=Math.max(p.width,p.height), radius=short/2
        const pasteShort=short*0.9, pasteLong=(long-short+2*Math.sqrt(radius**2-(pasteShort/2)**2))*0.99
        let width=p.width<p.height?pasteShort:pasteLong, height=p.width<p.height?pasteLong:pasteShort
        const rotation="ccw_rotation" in p ? p.ccw_rotation : 0
        if (Math.abs(rotation??0)%180===90) [width,height]=[height,width]
        panes.push({...e,width,height,x:p.x,y:p.y})
        return false
      }
    }
    return true
  })
  return [...filtered, ...panes]
}
