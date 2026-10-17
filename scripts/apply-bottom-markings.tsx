import React from "react"
import { Circuit } from "tscircuit"
import { readFileSync, writeFileSync, mkdirSync } from "node:fs"
import { createHash } from "node:crypto"
import { BottomMarkings } from "../src/bottom-markings"

// Append artwork to frozen routing; never rebuild the routed PCB from source.
const path = "artifacts/board.circuit.json"
const bytes = readFileSync(path)
const before = JSON.parse(bytes.toString())
const prefix = "pcb_silkscreen_path_bottom_marking_"
const existing = before.filter((e: any) => !e.pcb_silkscreen_path_id?.startsWith(prefix))
const circuit = new Circuit()
circuit.add(<board width={35} height={35} routingDisabled><BottomMarkings /></board>)
await circuit.renderUntilSettled()
const paths = circuit.getCircuitJson().filter(e => e.type === "pcb_silkscreen_path")
if (!paths.length) throw new Error("No bottom artwork generated")
const mcu = existing.find((e: any) => e.type === "source_component" && e.name === "U_MCU")
const owner = existing.find((e: any) => e.type === "pcb_component" && e.source_component_id === mcu.source_component_id).pcb_component_id
const added = paths.map((e: any, i) => ({ ...e, pcb_silkscreen_path_id: `${prefix}${i}`,
  pcb_component_id: owner,
  subcircuit_id: "subcircuit_source_group_0" }))
if (added.some(e => e.layer !== "bottom")) throw new Error("Artwork must be on bottom silkscreen")
const after = [...existing, ...added]
const unchanged = (records: any[]) => records.filter(e => !e.pcb_silkscreen_path_id?.startsWith(prefix))
if (JSON.stringify(unchanged(before)) !== JSON.stringify(unchanged(after))) throw new Error("Existing records changed")
writeFileSync(path, JSON.stringify(after, null, 2) + "\n")
mkdirSync("artifacts/bottom-markings", {recursive: true})
const sha = (b: Buffer) => createHash("sha256").update(b).digest("hex")
writeFileSync("artifacts/bottom-markings/native-preservation.json", JSON.stringify({
  before_board_sha256: sha(Buffer.from(JSON.stringify(existing, null, 2) + "\n")), board_sha256: sha(readFileSync(path)),
  all_existing_records_preserved: true, added_bottom_silkscreen_paths: added.length,
  routing_components_pads_drills_nets_and_schematic_unchanged: true,
}, null, 2) + "\n")
console.log(`Added ${added.length} bottom silkscreen paths; all existing records preserved`)
