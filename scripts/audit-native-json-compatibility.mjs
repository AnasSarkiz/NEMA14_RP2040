import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { checkRecords } from "./check-native-schema.mjs"

function inspect(path) {
  const bytes = readFileSync(path)
  const failures = checkRecords(JSON.parse(bytes))
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
  strict_full_order_schema_passed: order.failures.length === 0,
  legacy_native_schema_findings: native.failures,
  findings_by_type: counts,
  schema_findings_introduced_by_order_package: introduced,
  note: "Canonical metadata and native stencil records are checked against every installed Circuit JSON element schema; inherited compatibility errors are no longer accepted.",
}
writeFileSync("artifacts/jlcpcb-review/native-json-compatibility.json", JSON.stringify(receipt, null, 2) + "\n")
console.log(JSON.stringify({ strict_full_native_schema_passed: receipt.strict_full_native_schema_passed, inherited_findings: native.failures.length, introduced_findings: introduced.length }))
if (native.failures.length || order.failures.length) process.exitCode = 1
