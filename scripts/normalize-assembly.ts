import type { AnyCircuitElement } from "circuit-json"

/** Qualified top-side stencil policy; bare test pads and shell slots get no paste. */
export function normalizeAssembly(json: AnyCircuitElement[]): AnyCircuitElement[] {
  const sources = new Map(json.filter(e => e.type === "source_component").map(e => [e.source_component_id, e]))
  const parts = new Map(json.filter(e => e.type === "pcb_component").map(e => [e.pcb_component_id, e]))
  const result: any[] = json.filter(e => e.type !== "pcb_solder_paste")
  let index = 0
  for (const pad of json.filter(e => e.type === "pcb_smtpad") as any[]) {
    const part = parts.get(pad.pcb_component_id)
    const source = part && sources.get(part.source_component_id)
    if (!source || source.ftype === "simple_test_point" || part?.do_not_place) continue
    if (pad.layer !== "top") throw new Error("All fitted components must be top-side: " + source.name)
    const base = { type: "pcb_solder_paste", pcb_component_id: pad.pcb_component_id, pcb_smtpad_id: pad.pcb_smtpad_id, layer: pad.layer }
    if (pad.shape === "polygon") {
      const points = pad.points
      let area2 = 0, xsum = 0, ysum = 0
      for (let i = 0; i < points.length; i++) {
        const a = points[i], b = points[(i + 1) % points.length], cross = a.x * b.y - b.x * a.y
        area2 += cross; xsum += (a.x + b.x) * cross; ysum += (a.y + b.y) * cross
      }
      if (Math.abs(area2) < 1e-12) throw new Error("Degenerate polygon pad: " + pad.pcb_smtpad_id)
      const cx = xsum / (3 * area2), cy = ysum / (3 * area2)
      result.push({ ...base, pcb_solder_paste_id: `order_paste_${index++}`, shape: "polygon", points: points.map((p: any) => ({ x: cx + .7 * (p.x - cx), y: cy + .7 * (p.y - cy) })) })
      continue
    }
    if (!["rect", "pill", "rotated_pill"].includes(pad.shape)) throw new Error("Unreviewed fitted pad shape: " + pad.shape)
    const w = pad.width, h = pad.height
    let windows: number[][]
    if (["U_MCU", "U_DRV", "U_PD"].includes(source.name) && w > 2 && h > 2) {
      windows = [-1, 1].flatMap(dx => [-1, 1].map(dy => [pad.x + dx * w / 4, pad.y + dy * h / 4, w * Math.sqrt(.6) / 2, h * Math.sqrt(.6) / 2]))
    } else {
      let factor = .7
      while (Math.min(w, h) * factor / .1 < 1.5 || w * h * factor / (2 * (w + h) * .1) < .70) factor += .05
      if (factor > .95 + 1e-9) throw new Error("100 µm stencil release screen failed: " + source.name)
      windows = [[pad.x, pad.y, w * factor, h * factor]]
    }
    for (const [x, y, width, height] of windows) result.push({ ...base, pcb_solder_paste_id: `order_paste_${index++}`, shape: pad.shape, x, y, width, height, ccw_rotation: pad.ccw_rotation ?? 0, ...(pad.shape === "rect" ? {} : { radius: Math.min(width, height) / 2 }) })
  }
  return result as AnyCircuitElement[]
}
