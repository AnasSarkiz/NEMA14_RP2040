# Release-actuated motor terminal candidate — 1 November 2026

**Superseded:** The user reports $9.34 and requests WAGO instead. See
[WAGO decision](terminal-wago-2026-11-01.md). The catalog mirror price below
is not a JLCPCB quote and must not be used to promise a purchase price.

The user prefers deliberate wire release to the AVX twist-and-pull arrangement.
The preferred compact mechanical candidate is now one **Phoenix 1770979 /
PTSM 0,5/4-2,5-V THR R44**, [JLCPCB C3818616](https://jlcpcb.com/partdetail/PhoenixContact-1770979/C3818616).
It replaces the concept of two two-pole terminals with one four-pole housing.
This remains research; the active V2 source and ordered V1 are unchanged.

## Release and retention evidence

The [manufacturer-authored datasheet](https://asset.conrad.com/media10/add/160267/c1/-/en/000567976DS03/datasheet-567976-pcb-terminal-block-ptsm-05-4-25-v-thr-r44-1770979-phoenix-contact.pdf)
describes a spring-cage connection with a release mechanism and lists the
SZS 0,4×2,0 screwdriver as an operating accessory. It is not a lever-style
WAGO. Detailed actuation/tool access still needs sample verification.

The [current manufacturer specification](https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-ptsm-05-4-25-v-thr-r44-1770979)
reports a pull-out test result greater than **10 N for 0.2 mm² flexible wire**.
This applies to that specified conductor and test; it is not a measured
comparison with AVX or a guarantee for the factory motor leads.

## Fit

- Manufacturer body: **10.5 × 5 mm**, **10 mm installed height**. Total height
  including the 2.1 mm solder pins is 12.1 mm.
- Exact existing imported courtyard: **11.2552 × 5.5000 mm**, unmodified.
- Proposed anchor: **X −13.7 mm, Y +3.8 mm, rotation 90°**, top assembly.
- With that orientation, reserved area is **5.5000 × 11.2552 mm**, inside the
  former two-terminal region. No other component moves are required.
- The check finds no new top courtyard overlaps, preserves the mounting
  envelopes and clears bottom component/probe reserves with all eight plated
  pads. The minimum courtyard distance to a mounting-hole center is 4.2999 mm,
  against the required 3.2 mm screw-head-envelope radius.

Run `/workspace/.routing-venv/bin/python scripts/check-release-terminal-fit.py`.
It records source/definition hashes and writes the
[verification](../../artifacts/v2/connector-study/phoenix1770979-verification.json)
and [placement proposal](../../artifacts/v2/connector-study/phoenix1770979-placement.svg).
This is a 2D geometry screen, not generated replacement connectivity, routed
copper, detailed 3D, drill-to-trace DRC or manufacturing approval. Supplier CAD
and any pick-and-place-tab protrusions still need assembly review.

## Wire range and sourcing

Use the manufacturer's **bare flexible/stranded range, 0.2–0.5 mm²**, roughly
24–20 AWG, and **6 mm strip length**. The lower 0.14 mm² figure applies to solid
wire. The generic 26–20 AWG catalog label alone does not qualify 26 AWG bare
stranded motor leads. Factory motor lead CSA remains unspecified in the motor
drawing and therefore unconfirmed.

The 1 November JLCsearch mirror snapshot reports **zero stock**, with a part
price of **$1.3227 at 1–9**, **$0.9762 at 30–99**. These are catalog snapshots,
not a current reserved JLC quote. The direct JLC listing permits Economic and
Standard wave assembly. Procurement/preorder or consignment must be resolved
before adoption; the part has not been added to the active BOM.

The KEFA KF208V-2.54-4P / C49173465 remains a larger push-actuated budget
candidate, but no fit or factory wire qualification is claimed for it.

Imported footprint provenance: [JLCEDA / EasyEDA Official Library](https://easyeda.com),
[JLCEDA homepage](https://lceda.cn/). The existing supplier import is retained
without changing its geometry. The AVX video's ease of deliberate removal
does not itself establish poor accidental pull-out resistance.
