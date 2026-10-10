# Separate tscircuit installed assembly

`assembly.circuit.tsx` is the default-exported React/tscircuit assembly entry. `index.circuit.tsx` remains the controller circuit entry, and `index.circuit.json` remains its saved routed PCB. Open the assembly entry in tscircuit and select its 3D view. `assembly.circuit.json` is the generated self-contained assembly preview; all eight GLB models are embedded as data URLs so the scene needs no remote CAD downloads.

The scene uses official `assembly.device`, `assembly.subassembly` and `assembly.part` primitives. It includes the exact manufacturer's 14HM11-0404S motor, the fitted board, front-M3 carrier, motor harness with PHR-4/contacts/splices/wire service loops, barrier/clamp/supports, fasteners and both selected USB cables with reserved bends. `motorHarness` in the TSX records the four color/winding/pin assignments. Physical assembly models do not create electrical traces; the circuit entry remains the electrical authority.

## Why imported motor and cable assemblies

The official [motor docs](https://github.com/tscircuit/docs/blob/main/docs/elements/assembly-motor.mdx) currently support built-in NEMA8/17/23 and NEMA modelprinter specifications, with no imported CAD prop on `assembly.motor`. They explicitly recommend [assembly.subassembly](https://github.com/tscircuit/docs/blob/main/docs/elements/assembly-subassembly.mdx) for arbitrary motor CAD. This scene uses that documented fallback, rather than a representative NEMA17 or a false rear-thread attachment. Its exact motor/carrier relationship comes from the reviewed front-thread carrier STEP.

The [cable docs](https://github.com/tscircuit/docs/blob/main/docs/elements/assembly-cable.mdx) explain that native cable inference connects modeled connector endpoints; it does not create winding mappings, avoid obstacles or support route/length hints. The real motor has four factory leads and a qualified-on-prototype splice/PH harness, not a factory six-pin cable connector. An imported motor does not expose the native `MOTOR.wireside` endpoint. Therefore `MOTOR_HARNESS`, `PD_CABLE` and `DATA_CABLE` use the reviewed imported cable geometry, retaining the specified loops, restraint, real USB plug dimensions and clearances. No unsupported props or synthetic motor connector are introduced.

Manufacturer CAD and drawing-derived installation envelopes keep their existing status: factory motor/body and selected supplier models are imported; mating contacts/housing internal details, solder/insulation, wire bends and fasteners are reviewed envelopes. Exact header-post CAD discrepancy, insertion coupon, pull strength, certificates and physical fit remain pending. The board solid shows substrate/fitted component geometry; detailed copper/silkscreen remain in the electrical PCB and assembly drawings.

## Build and open

From either repository:

```sh
npm run assembly:assets   # optional: regenerate portable GLB assets from the bound reviewed STEP
npm run typecheck
npm run assembly:build
npm run assembly:check
npm run assembly:dev
```

Assets are under `assets/assembly/`. The asset manifest binds every group to the exact saved board, reviewed mounted STEP archive/member and generation script. CAD uses millimetres, the PCB midplane is Z0, and the normalization cancels CadQuery’s Y-up root transform without editing mesh bytes; tscircuit’s loader maps CAD to Scene3D `(x,z,y)` and its final glTF export uses `(-x,z,y)`. The build loads all eight models through `circuit-json-to-gltf`, checks bounding boxes/units/orientation against the native STEP, checks assembly errors, exports `artifacts/assembly-scene/installed-assembly.glb` and verifies unchanged PCB/Gerber hashes. It refuses stale mechanical inputs or edited assets.

The scene is a separate mechanical preview, not a new PCB revision or manufacturing package. Changing board placements requires rerunning the electrical and mechanical reviews before regenerating this scene. The installed assembly remains an unqualified prototype; see the operating envelope and bring-up checklist. Documentation snapshots used for this implementation are retained under `references/tscircuit-assembly/`.

The exported GLB retains indexed source meshes to avoid the much larger unindexed triangle export. Chromium/WebGL reviews the actual compact GLB, checks its dimensions and saves isometric, top, side, underside and controller-detail views under `artifacts/assembly-scene/`. Serve that folder with `python3 -m http.server --directory artifacts/assembly-scene` and open `viewer.html` for an interactive orbit/zoom view. This is a mechanical viewer, not electrical simulation.
