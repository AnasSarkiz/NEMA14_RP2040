# Compact motor terminal proposal — 31 October 2026

**Update, 1 November:** the user rejected the twist-and-pull AVX direction.
The [Phoenix release-actuated alternative](terminal-release-alternative-2026-11-01.md)
fits the original V2 connector area without moving the other parts. The AVX
study below is historical and is not the current recommendation.

The best compact candidate found is **KYOCERA AVX 009296004202906**,
four-position enclosed horizontal poke-home spring connector. Its newly found
[JLCPCB listing is C21619069](https://jlcpcb.com/partdetail/KyoceraAVX-009296004202906/C21619069),
with SMT assembly and Economic/Standard eligibility. Earlier research had not
located that listing; a related-product link exposed it.

This is a **placement proposal**, not an adopted part or manufacturing release.
The active V2 source still contains the Phoenix pair. Ordered V1 is untouched.

## Size, operation and cost

The [manufacturer drawing, page 5](https://www.mouser.com/datasheet/2/40/PHLPHorizontal_00_9296-3165243.pdf)
gives a **12 × 7 × 2.5 mm** four-position body, 3 mm pole pitch and eight SMT
lands. The study uses a manually defined **12.5 × 7.5 mm** courtyard, adding
0.25 mm to every body edge. This is an envelope for placement, not a converted
or electrically checked component footprint. All other component courtyards
are preserved from the active V2 supplier definitions.

The [manufacturer specification](https://datasheets.kyocera-avx.com/PHLPHorizontal_00-9296.pdf)
accepts **20–26 AWG solid or stranded conductors**, with insulation diameter at
most **1.6 mm**. Strip and insert the wire; removal uses twist-and-pull. It has
no lever or push-button and is rated for **three connection cycles**. This is
a candidate for wiring that normally remains connected; it is less suitable
for repeatedly swapping motors during bench testing. Retention, strip length,
wire preparation and removal need validation with a sample and the application
instructions before adoption.

A related JLC catalog page displayed approximately $0.30 for this MPN, but the
direct listing did not establish current price, orderability or stock. The
JLCsearch mirror returned no exact record. The retrieved
[DigiKey listing](https://www.digikey.com/en/products/detail/kyocera-avx/009296004202906/5161723)
displayed $0.83 at quantity one; this is a reference snapshot, not a JLC quote.
Allow about $1 for the part while obtaining an actual assembly quote. Consignment
may be necessary. Listing eligibility alone does not establish final assembly cost.

The factory 14HM11-0404S motor drawing still does not specify lead AWG or
insulation diameter. Direct motor-wire compatibility therefore remains unconfirmed.

## Placement result

[Proposal image](../../artifacts/v2/connector-study/placement.svg) and
[complete plan](../../artifacts/v2/connector-study/avx9296-plan.json):

- Keep the **34.5 × 34.5 mm** board and 26 mm mounting-hole pitch.
- Put the single four-wire housing on the left edge; wire entry faces outward.
- Move the bulk capacitor to the right and the compact buzzer to the left.
- Move the B-channel amplifier/shunt, temperature sensor, USB ESD device and
  affected small parts to clear those envelopes. Keep both BOOT recovery pads together.
- Retain all fitted parts and both encoder capacitors on top. Five bare debug
  probe pads and the optional DNP encoder reserve stay underneath.

The search used the existing CP-SAT placement model with adjusted anchors.
The recorded solution was subsequently checked independently with Shapely;
minor pad/passive changes and the TVS/data-diode position exchange were checked
against the same physical and proximity constraints. The validation receipt
records the base board source hash and the final proposal hash.

Run the read-only audit and regenerate the SVG:

```sh
/workspace/.routing-venv/bin/python scripts/verify-terminal-study.py
```

It checks board bounds, same-side courtyard overlap, Ø6.4 mm screw-head
envelopes, top-side fitted assembly, 60 existing/added proximity limits,
bottom probe/USB separation and four Ø1.6 mm insulation entry envelopes.
Proximity checks use Manhattan distance and allow 0.011 mm for the search's
0.01 mm rounding; they are not measured routed trace lengths.

No candidate electrical pads, netlist or copper are generated. The existing
unrouted V2 cannot be ordered. Detailed supplier CAD, actual wire fit/retention,
release access, bend radius, local power/ground and surge loops, USB routing,
Kelvin routing, thermal behavior, DRC and procurement remain outside this study.
The drawn coil labels are a proposed pin assignment, not verified connectivity.

## Other budget candidates checked

| Candidate | Evidence | Result |
|---|---|---|
| KEFA KF141R-2.54-4P / C475126 | About $0.38 mirror price; 13.31 × 14.30 mm imported courtyard; push-button; Economic wave assembly | Larger placement attempt infeasible with that tested anchor arrangement. Mirror stock zero; cached JLC listing and mirror disagree. Stranded range not separately qualified. |
| JILN JL141R-25404GA1 / C2922610 | About $0.41 mirror price; 13.215 × 13.10 mm imported courtyard; push-button; Economic wave assembly | Bounded search returned UNKNOWN, not proof of impossibility. Mirror stock zero; LCSC listing showed 100, which is not JLC assembly stock. |
| DEGSON DG250-2.5-04P-11-00A(H) / C49329097 | About $0.51 cached JLC price; 12 × 12.50 mm imported courtyard; 13 mm height; Economic wave assembly | Bounded search returned UNKNOWN. Manufacturer family supports 0.2–0.5 mm² flexible wire; smaller factory leads would need another option. |

These alternatives were imported only for research; none replaces the active
board connector. Supplier import geometry came from the
[JLCEDA / EasyEDA Official Library](https://easyeda.com),
[JLCEDA homepage](https://lceda.cn/).
