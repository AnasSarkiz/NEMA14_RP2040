import { readFileSync, writeFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { pcb_solder_paste } from "circuit-json"

const path = "artifacts/jlcpcb-review/order-source.circuit.json"
const bytes = readFileSync(path)
const paste = JSON.parse(bytes).filter(e => e.type === "pcb_solder_paste")
const errors = []
for (const aperture of paste) {
  const result = pcb_solder_paste.safeParse(aperture)
  if (!result.success) errors.push({ id: aperture.pcb_solder_paste_id, issues: result.error.issues })
}
const receipt = {
  passed: errors.length === 0,
  source_sha256: createHash("sha256").update(bytes).digest("hex"),
  native_Circuit_JSON_solder_paste_schema_checked: true,
  apertures_checked: paste.length,
  errors,
}
writeFileSync("artifacts/jlcpcb-review/order-paste-schema-verification.json", JSON.stringify(receipt, null, 2) + "\n")
console.log(JSON.stringify({ passed: receipt.passed, apertures_checked: paste.length, errors: errors.length }))
if (errors.length) process.exitCode = 1
