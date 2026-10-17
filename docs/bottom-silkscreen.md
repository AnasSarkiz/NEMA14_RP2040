# Bottom silkscreen, v1.13.1

The underside carries the official tscircuit wordmark and the exact warning:

> For evaluation only; not FCC approved for resale.

The warning wraps into two lines along the board edge. The wordmark uses the
letter outlines from tscircuit's official blue rounded-box logo, rendered as
positive white ink. Its original SVG is retained in
`references/branding/tscircuit-official-logo.svg`; source:
https://github.com/tscircuit/docs/blob/main/static/logo/logo.svg.

`src/bottom-markings.json` contains the final vector strokes and provenance.
`src/bottom-markings.tsx` renders them as native bottom silkscreen paths. All
strokes are 0.15 mm wide. Coordinates are mirrored for reading from the underside;
the Gerbers retain the standard common top-view coordinate system.
Bottom reference captions are also mirrored in the CAM coordinate system so they
read normally from the underside.

`scripts/apply-bottom-markings.tsx` compiles just this artwork and appends it to
the frozen routed board. Existing electrical, mechanical, schematic and artwork
records are preserved. The manufacturing exporter retains the same paths intact
and reserves their area before placing reference captions. It rejects artwork
inside the 0.151 mm mask guard, 0.101 mm drill guard or 0.101 mm board inset.

The preservation and CAM verification receipts are in `artifacts/bottom-markings`.
The warning is a board marking; it does not establish FCC authorization or change
the engineering conclusions in the final order review.
