# WAGO motor-terminal decision — 1 November 2026

The user rejected the Phoenix quote of $9.34 and explicitly selected WAGO.
Phoenix is no longer the intended V2 procurement choice.

The selected candidate is **one WAGO 233-204, four poles**,
[JLCPCB C3310192](https://jlcpcb.com/partdetail/WAGO-233204/C3310192).
It provides four push-button spring clamps for A+, A−, B+, B−. No mating
housing or crimp contacts are needed. Its JLCPCB listing supports Economic
and Standard wave assembly. This listing does not confirm current stock.

The [WAGO-authored datasheet](https://www1.futureelectronics.com/doc/WAGO/233-204.pdf)
specifies a **12.3 × 13.9 mm body, 15.5 mm above the PCB**, bare fine-stranded
conductors **0.08–0.5 mm² / 28–20 AWG**, and **5–6 mm stripping**.
This covers a broader stranded-wire range than the 2060 series. The actual
14HM11-0404S factory lead gauge and insulation size remain undocumented.

The 2060-452/998-404 / C2765055 was screened: it needs two two-pole housings,
accepts only 24–18 AWG stranded wire and is listed for Standard assembly only.
It is therefore not the selected Economic-assembly candidate. The tiny 2059
series is unsuitable for the required bare stranded-wire connection.

## Price and supply

No confirmed JLCPCB quote is available for the WAGO part. The third-party
catalog mirror reports zero stock and $2.4127 each at 1–9; this is historical
catalog data, not an offer, reserved stock or an assembled-board price.
It must not be presented as a guaranteed saving over the user's Phoenix quote.

## Import findings and implementation status

The exact C3310192 EasyEDA footprint was imported successfully. The unmodified
output is preserved as [raw-easyeda.tsx.txt](wago-233-204/raw-easyeda.tsx.txt),
with findings in [qualification.json](wago-233-204/qualification.json).
There are eight plated holes, two per pole. However:

- Imported drills are approximately Ø1.0 mm; WAGO specifies Ø1.1 mm +0.1 mm.
- Imported courtyard depth is 12.83 mm, smaller than the 13.9 mm body depth.
- Imported OBJ extents also do not directly match the manufacturer's body
  dimensions; the CAD variant and reference coordinates need reconciliation.

The import is quarantined rather than silently used in a board fit check.
The 34.5 × 34.5 mm layout needs repacking with the complete manufacturer body,
screw-head clearance, push-button/finger access and outward wire entry.
No WAGO placement or manufacturing signoff is claimed.

The active preview still shows the preceding Phoenix draft. The ordered V1,
active electrical source, generated preview and public tscircuit package are
unchanged by this research update. V2 remains unrouted.
