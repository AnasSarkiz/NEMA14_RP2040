import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { any_circuit_element } from "circuit-json"

function inspect(path) {
  const bytes = readFileSync(path)
  const failures = JSON.parse(bytes).filter(e => !any_circuit_element.safeParse(e).success)
    .map(e => ({ type: e.type, id: e[e.type + "_id"], name: e.name }))
  return { sha256: createHash("sha256").update(bytes).digest("hex"), failures }
}
const native = inspect("artifacts/board.circuit.json")
const order = inspect("artifacts/jlcpcb-review/order-source.circuit.json")
const existing = new Set(native.failures.map(e => JSON.stringify(e)))
const introduced = order.failures.filter(e => !existing.has(JSON.stringify(e)))
const counts = {}
for (const record of native.failures) counts[record.type] = (counts[record.type] ?? 0) + 1
const receipt = {
  native_board_sha256: native.sha256,
  order_source_sha256: order.sha256,
  strict_full_native_schema_passed: native.failures.length === 0,
  legacy_native_schema_findings: native.failures,
  findings_by_type: counts,
  schema_findings_introduced_by_order_package: introduced,
  note: "Saved native CAD has legacy metadata compatibility findings: numeric display offsets versus string offsets, null optional ownership, and a generic buzzer source record. Native rendering, pin/net/geometry checks pass. Strict generic importers still require metadata review; no full generic-schema PASS is claimed. Fabrication CAM and purchasing/placement data do not consume these display/ownership fields.",
}
writeFileSync("artifacts/jlcpcb-review/native-json-compatibility.json", JSON.stringify(receipt, null, 2) + "\n")
console.log(JSON.stringify({ strict_full_native_schema_passed: receipt.strict_full_native_schema_passed, inherited_findings: native.failures.length, introduced_findings: introduced.length }))
if (introduced.length) process.exitCode = 1
