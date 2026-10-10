import React from "react"
import { Circuit } from "tscircuit"
import { createHash } from "node:crypto"
import { spawnSync } from "node:child_process"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { runAllChecks } from "@tscircuit/checks"
import { convertCircuitJsonTo3D } from "circuit-json-to-gltf"
import Nema14Assembly, { motorHarness } from "../assembly.circuit"

const sha = (path: string) => createHash("sha256").update(readFileSync(path)).digest("hex")
const protectedPaths = ["index.circuit.tsx", "index.circuit.json", "artifacts/board.circuit.json", "artifacts/nema14-gerbers.zip"]
const before = Object.fromEntries(protectedPaths.map((p) => [p, sha(p)]))
const assets = JSON.parse(readFileSync("assets/assembly/asset-manifest.json", "utf8"))
if (assets.source_board_sha256 !== before["artifacts/board.circuit.json"]) throw new Error("Assembly assets do not match saved PCB")
for (const model of Object.values(assets.models) as Array<{path: string; sha256: string}>) {
  if (sha(model.path) !== model.sha256) throw new Error("Changed assembly asset: " + model.path)
}
if (sha("assets/assembly/models.json") !== assets.portable_models_json_sha256) throw new Error("Changed embedded models")
const circuit = new Circuit()
circuit.add(<Nema14Assembly />)
await circuit.renderUntilSettled()
const json = circuit.getCircuitJson()
const checks = await runAllChecks(json)
const problems = [...json, ...checks].filter((e) => e.type.endsWith("_error"))
if (problems.length) throw new Error("Assembly build/DRC errors: " + JSON.stringify(problems))
const names = json.filter((e) => e.type === "source_component").map((e) => e.name).sort()
const expectedNames = Object.keys(assets.models).sort()
if (JSON.stringify(names) !== JSON.stringify(expectedNames)) throw new Error("Missing or duplicate assembly groups")
const scene = await convertCircuitJsonTo3D(json, { drawFauxBoard: false, showBoundingBoxes: false })
if (scene.boxes.length !== expectedNames.length) throw new Error("Assembly model count mismatch")
let triangles = 0
const lower = [Infinity, Infinity, Infinity], upper = [-Infinity, -Infinity, -Infinity]
const models = scene.boxes.map((box) => {
  if (!box.mesh?.triangles.length) throw new Error("A CAD model failed to load")
  triangles += box.mesh.triangles.length
  if (box.rotation && Object.values(box.rotation).some((v) => Math.abs(v) > 1e-8)) throw new Error("Unexpected assembly rotation")
  for (const triangle of box.mesh.triangles) for (const vertex of triangle.vertices) {
    for (const [i, axis] of ["x", "y", "z"].entries()) {
      const value = vertex[axis as "x" | "y" | "z"] + box.center[axis as "x" | "y" | "z"]
      lower[i] = Math.min(lower[i], value); upper[i] = Math.max(upper[i], value)
    }
  }
  return { label: box.label, triangles: box.mesh.triangles.length, center: box.center, bbox: box.mesh.boundingBox }
})
// Native CAD is Z-up. The tscircuit loader uses Scene3D(x,z,y); its final glTF export uses(-x,z,y).
const n: number[] = assets.native_mounted_bbox_mm
const expectedBounds = [n[0], n[2], n[1], n[3], n[5], n[4]]
const actualBounds = [...lower, ...upper]
if (actualBounds.some((v, i) => !Number.isFinite(v) || Math.abs(v - expectedBounds[i]) > 0.08)) {
  throw new Error("Assembly units/orientation/bounds changed: " + JSON.stringify({actualBounds, expectedBounds}))
}
mkdirSync("artifacts/assembly-scene", {recursive: true})
writeFileSync("assembly.circuit.json", JSON.stringify(json, null, 2) + "\n")
const compact = spawnSync(process.execPath, ["scripts/export-assembly-glb.js"], {stdio: "inherit"})
if (compact.status !== 0) throw new Error("Indexed assembly GLB export failed")
for (const path of protectedPaths) if (sha(path) !== before[path]) throw new Error("Assembly changed protected PCB output: " + path)
writeFileSync("artifacts/assembly-scene/build-review.json", JSON.stringify({
  source_board_sha256: before["artifacts/board.circuit.json"],
  assembly_entry_sha256: sha("assembly.circuit.tsx"),
  assembly_json_sha256: sha("assembly.circuit.json"),
  installed_glb_sha256: sha("artifacts/assembly-scene/installed-assembly.glb"),
  asset_manifest_sha256: sha("assets/assembly/asset-manifest.json"),
  indexed_export_review_sha256: sha("artifacts/assembly-scene/indexed-export-review.json"),
  model_count: models.length, triangles, models,
  native_expected_scene_bounds_mm: expectedBounds, rendered_scene_bounds_mm: actualBounds,
  expected_export_glTF_bounds_mm: [-n[3],n[2],n[1],-n[0],n[5],n[4]],
  assembly_errors: problems, warnings: checks.filter((e) => e.type.endsWith("_warning")),
  winding_map: motorHarness, protected_PCB_hashes_unchanged: before,
  hardware_fit_verified: false, units_and_orientation_checked: true,
}, null, 2) + "\n")
console.log("Assembly built:", models.length, "loaded CAD groups;", triangles, "triangles; PCB/Gerbers unchanged")
