import React from "react"
import objPath from "./A_1770979.obj"
import stepPath from "./A_1770979.step"
import type { ChipProps } from "@tscircuit/props"

const pinLabels = {
  pin1: ["pin1"],
  pin2: ["pin2"],
  pin3: ["pin3"],
  pin4: ["pin4"]
} as const

export const A_1770979 = (props: ChipProps<typeof pinLabels>) => {
  return (
    <chip
      pinLabels={pinLabels}
      supplierPartNumbers={{
  "jlcpcb": [
    "C3818616"
  ]
}}
      manufacturerPartNumber="1770979"
      footprint={<footprint>
        <platedhole  portHints={["pin1"]} pcbX="-3.750056mm" pcbY="1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin2"]} pcbX="-1.250188mm" pcbY="1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin3"]} pcbX="1.249934mm" pcbY="1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin3"]} pcbX="1.249934mm" pcbY="-1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin2"]} pcbX="-1.250188mm" pcbY="-1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin1"]} pcbX="-3.750056mm" pcbY="-1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin4"]} pcbX="3.750056mm" pcbY="-1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<platedhole  portHints={["pin4"]} pcbX="3.750056mm" pcbY="1.550035mm" outerDiameter="1.7999964mm" holeDiameter="1.1999976mm" shape="circle" />
<silkscreenpath route={[{"x":-4.433696999999938,"y":-2.4500331999998934},{"x":-6.150305199999934,"y":-2.4500331999998934}]} />
<silkscreenpath route={[{"x":-1.933828999999946,"y":-2.4500331999998934},{"x":-3.0666689999999335,"y":-2.4500331999998934}]} />
<silkscreenpath route={[{"x":0.5662929999999733,"y":-2.4500331999998934},{"x":-0.5668009999999413,"y":-2.4500331999998934}]} />
<silkscreenpath route={[{"x":3.06641500000012,"y":-2.4500331999998934},{"x":1.9333210000000918,"y":-2.4500331999998934}]} />
<silkscreenpath route={[{"x":4.449673599999983,"y":-2.438069799999994},{"x":4.449673599999983,"y":-2.4500331999998934},{"x":4.433443000000011,"y":-2.4500331999998934}]} />
<silkscreenpath route={[{"x":4.449673599999983,"y":0.6619240000001128},{"x":4.449673599999983,"y":-0.6620001999999658}]} />
<silkscreenpath route={[{"x":4.275658200000066,"y":2.549956800000132},{"x":4.449673599999983,"y":2.549956800000132},{"x":4.449673599999983,"y":2.437993600000027}]} />
<silkscreenpath route={[{"x":1.7755361999999195,"y":2.549956800000132},{"x":3.224199800000065,"y":2.549956800000132}]} />
<silkscreenpath route={[{"x":-0.7245857999998861,"y":2.549956800000132},{"x":0.7240778000000319,"y":2.549956800000132}]} />
<silkscreenpath route={[{"x":-3.2244537999998784,"y":2.549956800000132},{"x":-1.7760442000000012,"y":2.549956800000132}]} />
<silkscreenpath route={[{"x":-6.150305199999934,"y":-2.4500331999998934},{"x":-6.150305199999934,"y":2.549956800000132},{"x":-4.275912199999993,"y":2.549956800000132}]} />
<silkscreentext text="{NAME}" pcbX="-0.725678mm" pcbY="3.590165mm" anchorAlignment="center" fontSize="1mm" />
<fabricationnotepath route={[{"x":-6.150305199999934,"y":2.549956800000132},{"x":-6.150305199999934,"y":-2.4500331999998934},{"x":-4.850307799999996,"y":-2.4500331999998934},{"x":-4.850307799999996,"y":2.549956800000132},{"x":-6.150305199999934,"y":2.549956800000132}]} strokeWidth="0.254mm" />
<courtyardoutline outline={[{"x":-6.355118599999855,"y":2.7499442000000727},{"x":4.9000542,"y":2.7499442000000727},{"x":4.9000542,"y":-2.7500458000000663},{"x":-6.355118599999855,"y":-2.7500458000000663},{"x":-6.355118599999855,"y":2.7499442000000727}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 0,
        modelOriginPosition: { x: -4.394874700000055, y: 2.5000507999998263, z: -10.0000042 },
      }}
      {...props}
    />
  )
}