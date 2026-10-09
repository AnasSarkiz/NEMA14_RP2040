# Native A4 schematic review — service revision

The current prepared schematic uses 14 native A4 landscape sheets297×210mm, numbered physical pins/named nets, NC marks and chip-purpose notes. Every sheet was opened in the read-only project Chromium UI; reference coverage and A4 dimensions were checked with0 browser errors. `tsci check schematic-placement artifacts/final-source.circuit.json` exits0 with zero findings. See `artifacts/validation/service-schematic-ui/review.json`, per-page screenshots and `service-cli-results.json`; their hashes bind the current source/delivery.

The UI displays native tscircuit SVGs and actual CLI findings. It is a project review UI; no official IDE/WebGPU analyzer execution, circuit simulation or electrical qualification is claimed. Entry-only layout and prepared multi-sheet schematic are different build stages. The prepared sheets are the saved, rendered and reviewed release artifact.

Run `python3 scripts/check-a4-browser.py` for the browser check and `/workspace/.routing-venv/bin/python scripts/export-a4-pdf.py` for the combinedA4PDF. All fitted 68 parts have supplier import identities and retained assets; the manufacturer-derived JST drilling and corrected capacitor model are explicit exceptions. Physical/native pin mapping is audited independently from symbol presentation.
