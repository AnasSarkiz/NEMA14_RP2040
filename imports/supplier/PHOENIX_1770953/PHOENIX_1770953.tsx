import React from "react"
import objPath from "./PHOENIX_1770953.envelope.obj"

// Manufacturer 1770953 drawing + KiCad PTSM-0,5-2-2.5-V-THR land pattern.
// KiCad XY origin is translated (-0.4,+1.6) and Y inverted to centre the body.
// Four explicit PCB contacts represent two electrical poles. CAD is a dimensioned
// body/pin envelope, not a supplier detailed solid. See references/v2/terminal-selection.md.
export const PHOENIX_1770953 = (props:any) => <connector
  pinCount={4}
  manufacturerPartNumber="1770953"
  supplierPartNumbers={{jlcpcb:["C3817232"]}}
  pinLabels={{pin1:["PLUS"],pin2:["PLUS_2"],pin3:["MINUS"],pin4:["MINUS_2"]}}
  footprint={<footprint insertionDirection="from_above">
    <platedhole portHints={["pin1"]} pcbX={-.4} pcbY={-1.6} shape="circle" outerDiameter={2} holeDiameter={1.2} />
    <platedhole portHints={["pin2"]} pcbX={-.4} pcbY={1.5} shape="circle" outerDiameter={2} holeDiameter={1.2} />
    <platedhole portHints={["pin3"]} pcbX={2.1} pcbY={-1.6} shape="circle" outerDiameter={2} holeDiameter={1.2} />
    <platedhole portHints={["pin4"]} pcbX={2.1} pcbY={1.5} shape="circle" outerDiameter={2} holeDiameter={1.2} />
    <silkscreenpath route={[{x:-2.85,y:-2.6},{x:-2.85,y:2.6},{x:-1.5,y:2.6}]} />
    <silkscreenpath route={[{x:-2.85,y:-2.6},{x:-1.5,y:-2.6}]} />
    <courtyardoutline outline={[{"x":-3.25,"y":-3.01},{"x":3.25,"y":-3.01},{"x":3.25,"y":3},{"x":-3.25,"y":3},{"x":-3.25,"y":-3.01}]} />
  </footprint>}
  cadModel={{objUrl:objPath,modelOriginPosition:{x:0,y:0,z:0}}}
  {...props}
/>
