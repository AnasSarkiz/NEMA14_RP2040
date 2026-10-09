import React from "react"
const objPath = "https://modelcdn.tscircuit.com/easyeda_models/assets/C131334.obj?uuid=3b95b8b4d5d24ff4a871a43c952e432a"
const stepPath = "https://modelcdn.tscircuit.com/easyeda_models/assets/C131334.step?uuid=3b95b8b4d5d24ff4a871a43c952e432a"
import type { ChipProps } from "@tscircuit/props"

const pinLabels = {
  pin1: ["pin1"],
  pin2: ["pin2"],
  pin3: ["pin3"],
  pin4: ["pin4"]
} as const

export const B4B_PH_K_S_LF__SN_ = (props: ChipProps<typeof pinLabels>) => {
  return (
    <chip
      pinLabels={pinLabels}
      supplierPartNumbers={{
  "jlcpcb": [
    "C131334"
  ]
}}
      manufacturerPartNumber="B4B-PH-K-S(LF)(SN)"
      footprint={<footprint>
        <platedhole  portHints={["pin2"]} pcbX="0.999998mm" pcbY="-0.550037mm" outerDiameter="1.5999968mm" holeDiameter="0.999998mm" shape="circle" />
<platedhole  portHints={["pin1"]} pcbX="2.999994mm" pcbY="-0.550037mm" outerDiameter="1.5999968mm" holeDiameter="0.999998mm" shape="circle" />
<platedhole  portHints={["pin3"]} pcbX="-0.999998mm" pcbY="-0.550037mm" outerDiameter="1.5999968mm" holeDiameter="0.999998mm" shape="circle" />
<platedhole  portHints={["pin4"]} pcbX="-2.999994mm" pcbY="-0.550037mm" outerDiameter="1.5999968mm" holeDiameter="0.999998mm" shape="circle" />
<silkscreencircle pcbX="4.285996mm" pcbY="-1.566037mm" radius="0.359156mm" />
<silkscreenrect pcbX="0mm" pcbY="0mm" width="9.99998mm" height="4.500118mm" strokeWidth="0.254mm" />
<silkscreentext text="{NAME}" pcbX="0.009398mm" pcbY="3.243963mm" anchorAlignment="center" fontSize="1mm" />
<courtyardoutline outline={[{"x":-5.200002799999993,"y":2.6999569999999267},{"x":5.199977399999966,"y":2.6999569999999267},{"x":5.199977399999966,"y":-2.500033599999938},{"x":-5.200002799999993,"y":-2.500033599999938},{"x":-5.200002799999993,"y":2.6999569999999267}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 180,
        modelOriginPosition: { x: 2.9999872999999297, y: -0.5500383000000056, z: -0.000005999999999950489 },
      }}
      {...props}
    />
  )
}