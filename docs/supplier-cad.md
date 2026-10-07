# JLCPCB imports and printable schematics

Every fitted component uses a supplier component created with `tsci import --jlcpcb --download --use-exact-footprint C<number>`. `src/jlcpcb-catalog.json` maps every reference to its exact JLCPCB part and records original import/model hashes. The active component resolver in `src/supplier-parts.tsx` renders the imported JSX; it rejects custom footprint and CAD overrides. Unused generic component files have been removed.

`imports/supplier/` contains the native TSX, unchanged original `.tsx.original`, OBJ and STEP files. Active TSX only adds React compatibility, public GitHub model URLs and a CAD anchor correction for asymmetric pad bounds. Imported footprint JSX is checked byte for byte against the original. No model vertices or supplier footprints have been resized or translated. Public raw GitHub URLs keep large CAD assets outside the registry upload limit.

Both USB receptacles are **C165948 / TYPE-C-31-M-12**. All 16 numbered supplier contacts, including four shield tabs, use the actual land pattern. Their model mating planes are exactly X = −17.5 and +17.5 mm. Model bounds are checked against native courtyards. Coordinate checks do not establish physical rear-motor fit.

Motor, debug and BOOT connections are bare PCB solder interfaces. They have no fitted component to import or model. The four mounting holes are PCB features.

The exact sense resistors are **C2930216 / FRL0805FR240TS**, 0.24 Ω, 1%, 125 mW. A 39k/10k VREF divider sets about 0.351 A nominal peak phase current; estimated sense dissipation is 29.5 mW. The bulk capacitor is **C72522 / RVT1V470M0605**, 47 µF, 35 V. Verify current, thermal behavior and capacitor bias on an assembled prototype.

Native numbered landscape A4 sheets include every physical pin and chip-purpose text. `report-presentation.py` verifies original imported footprint JSX, supplier IDs/MPNs, both CAD assets and hashes, 3D placement bounds, USB opening planes, A4 dimensions and pin/net coverage.

CH224K supply resistor R_PD uses **C441922 / ERJPA3F1001V**, 1 kΩ, 0603, 0.25 W, with its exact imported land pattern. The higher power rating covers dissipation from dropping the requested motor supply to PD logic VDD.
