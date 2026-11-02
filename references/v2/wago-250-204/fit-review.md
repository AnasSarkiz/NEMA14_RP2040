# WAGO 250-204 fit review — 2 November 2026

**The 250-204 does not fit the existing V2 placement.** This is a fixed-layout
assessment, not proof that a redesigned 34.5 × 34.5 mm board is impossible.
No electrical source, active placement, V1 order or public package was changed.

## Part and electrical suitability

- Part: WAGO 250-204, [JLCPCB C2765063](https://jlcpcb.com/partdetail/WAGO_INNOVATIVECONNECTIONS-250204/C2765063).
- [Manufacturer-authored datasheet](https://datasheet.octopart.com/250-204-WAGO-datasheet-164888061.pdf), revision 4 September 2020:
  body **15.5 × 12 mm**, **13.1 mm above PCB**, four isolated poles,
  **3.5 mm pitch**, four staggered solder pins, push-button wire connection,
  and **45° wire entry**. IEC current rating is 8 A; ratings vary by approval.
- Bare fine-stranded conductor range: **0.2–1.5 mm² / 24–16 AWG**.
  Strip **8.5–9.5 mm**. Bare stranded wire is inserted with the button pressed;
  push-in insertion without opening the spring applies to solid/ferruled wire.
- The rating is adequate for the 0.4 A/phase 14HM11-0404S motor. Its actual
  factory wire CSA and insulation diameter remain undocumented, so connector
  compatibility with those leads is not confirmed.
- JLCPCB lists Economic and Standard wave assembly. The previous price/stock
  comparison contained conflicting, dated catalog figures; no live supply or
  reserved purchase quote is established by this fit check.

## Geometry check

The exact EasyEDA import was downloaded using `tsci import C2765063 --download
--use-exact-footprint`. Its unmodified TSX is preserved as
[raw-easyeda.tsx.txt](raw-easyeda.tsx.txt), rather than added to the active BOM.
The imported full courtyard is **16.0000 × 12.5000 mm**, or **200.0 mm²**.
The two current Phoenix courtyards occupy **78.13 mm²** together: the new
terminal reserves **2.56 times** that area, before wire or finger access.

The check removes both existing motor-terminal courtyards and retains all
other 98 top courtyards. All are axis-aligned rectangles. For both the nominal
manufacturer body and imported courtyard, it calculates the continuous region
of permissible rectangle centers within the PCB, then subtracts each obstacle's
rectangular Minkowski expansion. The remaining region is empty at 0° and 90°.
180°/270° have the same housing envelopes. This establishes no clear location
in the existing layout at those orientations, even before screw-head and wire
access restrictions are added. It does not evaluate arbitrary diagonal placement
or claim a newly packed layout cannot work.

The illustration places the complete courtyard near the former connector area,
inside the board and clear of the four Ø6.4 mm screw-head envelopes. It overlaps
14 existing courtyards, including **C_BULK, U_IA, U_PD and C_ENCODER_BULK**.
Those are collisions at that illustrative location, not a proven minimum number
of components that any redesign must move. Moving the current-sense amplifier
also requires preserving its shunt/input and decoupling proximity constraints.

Run `/workspace/.routing-venv/bin/python scripts/check-wago250204-fit.py`.

- [Geometry report](../../../artifacts/v2/connector-study/wago250204-verification.json)
- [Illustrated conflicts](../../../artifacts/v2/connector-study/wago250204-fit.svg)

This review does not approve pad numbering, latest drill tolerances, a replacement
netlist, detailed 3D/button access, bottom solder-pin clearance, thermal behavior
or routed-board manufacturing. V2 remains an unrouted engineering draft.
