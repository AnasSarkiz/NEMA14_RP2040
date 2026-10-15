/** Canonical schema metadata without changing physical coordinates or nets. */
export function normalizeMetadata(json: any[]) {
  const mcu = json.find(e => e.type === "source_component" && e.name === "U_MCU")
  const graphicOwner = json.find(e => e.type === "pcb_component" && e.source_component_id === mcu?.source_component_id)?.pcb_component_id
  for (const e of json) {
    for (const field of ["display_offset_x", "display_offset_y"]) {
      if (typeof e[field] === "number") e[field] = String(e[field])
    }
    for (const field of Object.keys(e)) {
      if (field.endsWith("_id") && e[field] === null) delete e[field]
    }
    // Board captions retain absolute coordinates; this schema requires a
    // component owner for silk circles/text. Associate them with the controller.
    if (["pcb_silkscreen_circle", "pcb_silkscreen_text"].includes(e.type) && !e.pcb_component_id) e.pcb_component_id = graphicOwner
    // The installed Circuit JSON schema has no simple_buzzer variant. Keep
    // its real MPN, numbered terminals and buzzer schematic; use generic pinout.
    if (e.type === "source_component" && e.name === "BZ1") e.ftype = "simple_pinout"
  }
  return json
}
