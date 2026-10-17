import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"
import * as schemas from "circuit-json"
export function checkRecords(records) {
  return records.flatMap((e, index) => {
    const schema = e.type === "source_component" ? schemas.any_source_component : schemas[e.type] ?? schemas.any_circuit_element
    const result = schema.safeParse(e)
    return result.success ? [] : [{ index, type: e.type, id: e[e.type + "_id"], issues: result.error.issues }]
  })
}
if (process.argv[1]?.endsWith("check-native-schema.mjs")) {
  const file = process.argv[2] ?? "artifacts/board.circuit.json", bytes = readFileSync(file), records = JSON.parse(bytes)
  const errors = checkRecords(records)
  const report = { passed: errors.length === 0, source_sha256: createHash("sha256").update(bytes).digest("hex"), board_sha256: createHash("sha256").update(bytes).digest("hex"), records_checked: records.length, no_inherited_schema_errors_accepted: true, errors }
  writeFileSync("artifacts/engineering-fixes/schema-verification.json", JSON.stringify(report, null, 2) + "\n")
  console.log(JSON.stringify({ passed: report.passed, records_checked: records.length, error_count: errors.length }))
  if (errors.length) process.exitCode = 1
}
