/** Align drawn box-pin stems without moving pin endpoints or any wiring. */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs"
import { createHash } from "node:crypto"

const sha = (value: string | Buffer) => createHash("sha256").update(value).digest("hex")
const boardBytes = readFileSync("index.circuit.json")
const assemblyBytes = readFileSync("assembly.circuit.json")
const board: any[] = JSON.parse(boardBytes.toString())
const assembly: any[] = JSON.parse(assemblyBytes.toString())
if (!boardBytes.equals(readFileSync("artifacts/board.circuit.json"))) throw Error("Board mirrors differ")
if (JSON.stringify(assembly.slice(0, board.length)) !== JSON.stringify(board)) throw Error("Assembly board prefix differs")
const original = structuredClone(board)
const components = new Map(board.filter(e => e.type === "schematic_component").map(e => [e.schematic_component_id, e]))
const names = new Map(board.filter(e => e.type === "source_component").map(e => [e.source_component_id, e.name]))
const changes: any[] = []
for (const port of board.filter(e => e.type === "schematic_port")) {
  const component = components.get(port.schematic_component_id)
  if (!component || component.symbol_name || component.is_box_with_pins === false || !port.distance_from_component_edge) continue
  const horizontal = ["left", "right"].includes(port.facing_direction)
  const axis = horizontal ? "x" : "y", dimension = horizontal ? "width" : "height"
  const distance = Number((Math.abs(port.center[axis] - component.center[axis]) - component.size[dimension] / 2).toFixed(9))
  if (distance <= 0) throw Error("Box pin endpoint lies inside its symbol")
  if (Math.abs(distance - port.distance_from_component_edge) <= 1e-8) continue
  changes.push({ component: names.get(component.source_component_id), pin: port.pin_number,
    label: port.display_pin_label, old_stem_length: port.distance_from_component_edge, new_stem_length: distance })
  port.distance_from_component_edge = distance
}
if (!changes.length) { console.log("All rendered box pin stems already align"); process.exit(0) }
// The record count/order and every field other than these display lengths stay exact.
const withoutStemLengths = (records: any[]) => records.map(e => {
  const copy = structuredClone(e)
  if (copy.type === "schematic_port") delete copy.distance_from_component_edge
  return copy
})
if (JSON.stringify(withoutStemLengths(board)) !== JSON.stringify(withoutStemLengths(original))) throw Error("Unexpected drawing/electrical edit")
const nonSchematic = (records: any[]) => records.filter(e => !e.type.startsWith("schematic_"))
if (JSON.stringify(nonSchematic(board)) !== JSON.stringify(nonSchematic(original))) throw Error("Non-schematic records changed")
const output = JSON.stringify(board) + "\n"
const updatedAssembly = [...board, ...assembly.slice(board.length)]
const assemblyOutput = JSON.stringify(updatedAssembly) + "\n"
for (const path of ["index.circuit.json", "artifacts/board.circuit.json"]) writeFileSync(path, output)
for (const path of ["assembly.circuit.json", "artifacts/top-assembly/assembly-preview.circuit.json"]) writeFileSync(path, assemblyOutput)
mkdirSync("artifacts/schematic-pin-alignment", { recursive: true })
const proof = { passed: true, baseline_version: "1.12.1", scope: "schematic pin display lengths only",
  before_board_sha256: sha(boardBytes), board_sha256: sha(output),
  before_assembly_sha256: sha(assemblyBytes), assembly_sha256: sha(assemblyOutput),
  non_schematic_records_sha256: sha(JSON.stringify(nonSchematic(board))),
  electrical_and_PCB_and_CAD_records_unchanged: true, pin_endpoints_and_all_wires_unchanged: true,
  mechanical_assembly_records_unchanged: true, changes }
writeFileSync("artifacts/schematic-pin-alignment/verification.json", JSON.stringify(proof, null, 2) + "\n")
console.log(JSON.stringify({ passed: true, changed_ports: changes.length, components: [...new Set(changes.map(c => c.component))] }))
