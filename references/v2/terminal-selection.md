# V2 compact terminal selection

Two **Phoenix 1770953 / C3817232**, PTSM 0,5/2-2,5-V THR R44, replace the
single four-pole 1770979 candidate. Each two-pole body is **5.5 × 5 × 10 mm
above the board**, rather than 10.5 × 5 × 10 mm. Splitting the poles improves
placement flexibility; it does **not** reduce the combined courtyard area or
price. J_MOTOR_A carries A+/A−; J_MOTOR_B carries B+/B−. Wire entry and release
access are from above. All fitted components remain assembled from the top.

## Primary dimensions and footprint provenance

- Manufacturer datasheet: [1770953](https://media.digikey.com/pdf/Data%20Sheets/Phoenix%20Contact%20PDFs/1770953.pdf), cached as `phoenix-1770953.pdf`.
- KiCad reference: [PTSM-0,5-2-2.5-V-THR footprint](https://github.com/KiCad/kicad-footprints/blob/master/TerminalBlock_Phoenix.pretty/TerminalBlock_Phoenix_PTSM-0%2C5-2-2.5-V-THR_1x02_P2.50mm_Vertical.kicad_mod), cached alongside the PDF. KiCad library license: [CC-BY-SA 4.0 with library exception](https://www.kicad.org/libraries/license/).
- Drawing confirms 2.5 mm pole pitch, 3.1 mm row pitch, four Ø1.2 mm drills,
  0.3 × 0.8 mm pins, 2.1 mm solder-pin length and 10 mm installed height.
- `PHOENIX_1770953.tsx` translates the KiCad coordinates by x−0.4, inverts Y
  and shifts it by −1.6 to put the body centre at the placement anchor.
  Both contacts per pole are explicit ports. Each has a Ø2 mm round annular
  copper pad (including the originally rectangular KiCad pin-1 pads).
- Courtyard is the complete KiCad 6.5 × 6.01 mm rectangle. No courtyard is
  shortened to obtain a fit.
- Exact EasyEDA import for C3817232 was unavailable. The OBJ is explicitly a
  **dimensioned body/pin envelope**, not a detailed manufacturer CAD model.
  Do not use that envelope as a latch, insertion, tool or tolerance model.

## Wire and procurement qualification

The manufacturer's bare-stranded range is **0.2–0.5 mm²**, approximately
24–20 AWG, with **6 mm stripping length**. The solid-wire minimum of 0.14 mm²
does not apply to stranded motor leads. Factory motor lead CSA and insulation
size remain unknown, so direct-wire compatibility is **not confirmed**.
The earlier 28 AWG SH pigtails do not satisfy this terminal's stranded minimum.

The JLCsearch snapshot of C3817232 reports **zero stock**. This is not live
JLCPCB stock, and a catalog/assembly listing does not reserve components.
Procurement/preorder or consignment must be confirmed before an order.

Other checked candidates include Phoenix 1702474/C17258392 (SMT land pattern
15.8 × 11.6 mm, larger), WAGO 233-204/C3310192 (body 12.3 × 13.9 mm, larger),
and AVX C5348524 (small individual contacts, but four imported courtyards total
more area and exposed contacts require a different mechanical arrangement).
AVX C19724004 is a bottom-wire-entry contact and was not selected.
