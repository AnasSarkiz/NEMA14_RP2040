# Lean tscircuit publication

Publish only 13 files: native PCB and assembly Circuit JSON, their two compiled
viewer copies, Gerbers, JLCPCB BOM and CPL, the schematic PDF, the bottom
silkscreen preview, README, package/viewer configuration and a short verification
record. The compiled copies are required by tscircuit's preview API.

Keep the complete project, supplier models, datasheets, full qualification
receipts, routing tools and historical reports in GitHub. Native CAD models use
the existing byte-verified GitHub URLs; the registry does not need model copies.

`npm run publish:tscircuit -- --stage-only` shows the exact payload. Local
qualification gates remain mandatory. Publishing and `--prune` require a verified
full GitHub source snapshot before any registry file removal. Pruning affects only
the current package version and never deletes workspace or GitHub files.
