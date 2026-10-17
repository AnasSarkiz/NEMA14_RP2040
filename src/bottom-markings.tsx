import React from "react"
import markings from "./bottom-markings.json"

// Mirrored vector strokes read correctly when viewed from the underside.
// The same native paths are retained intact in the qualified fabrication CAM.
export function BottomMarkings() {
  return <>{markings.groups.flatMap((group, gi) => group.routes.map((route, ri) =>
    <React.Fragment key={`${gi}-${ri}`}><silkscreenpath layer="bottom" strokeWidth={group.stroke_width_mm}
      route={route.map(([x, y]) => ({ x, y }))} /></React.Fragment>
  ))}</>
}
