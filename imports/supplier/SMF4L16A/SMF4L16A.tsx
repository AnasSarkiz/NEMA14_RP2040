import React from "react"
const objPath = new URL("./SMF4L16A.obj", import.meta.url).href
const stepPath = new URL("./SMF4L16A.step", import.meta.url).href
import type { ChipProps } from "@tscircuit/props"

const pinLabels = {
  pin1: ["A"],
  pin2: ["K"]
} as const

export const SMF4L16A = (props: ChipProps<typeof pinLabels>) => {
  return (
    <chip
      pinLabels={pinLabels}
      symbol={
        <symbol>
          <schematicpath svgPath="M 0 0.14 L -0.2 0 L 0 -0.14 Z" strokeColor="#880000" />
          <schematicpath points={[{"x":-0.2,"y":0},{"x":-0.3,"y":0}]} strokeColor="#880000" />
          <schematicpath points={[{"x":0.1,"y":0},{"x":0,"y":0}]} strokeColor="#880000" />
          <schematicpath points={[{"x":-0.24,"y":0.1},{"x":-0.24,"y":0.14},{"x":-0.2,"y":0.14},{"x":-0.2,"y":-0.14},{"x":-0.16,"y":-0.14},{"x":-0.16,"y":-0.1}]} strokeColor="#880000" />
          <port name="pin2" pinNumber={2} aliases={["K"]} direction="left" schX={-0.5} schY={0} schStemLength={0.2} />
          <port name="pin1" pinNumber={1} aliases={["A"]} direction="right" schX={0.3} schY={0} schStemLength={0.2} />
          <schematictext schX={-0.1} schY={0.34} text="{NAME}" fontSize={0.2} anchor="bottom_center" />
        </symbol>
      }
      supplierPartNumbers={{
  "jlcpcb": [
    "C1973135"
  ]
}}
      manufacturerPartNumber="SMF4L16A"
      footprint={<footprint>
        <smtpad portHints={["pin1"]} pcbX="-1.624076mm" pcbY="0mm" width="1.2079986mm" height="1.3299948mm" shape="rect" />
<smtpad portHints={["pin2"]} pcbX="1.624076mm" pcbY="0mm" width="1.2079986mm" height="1.3299948mm" shape="rect" />
<silkscreenpath route={[{"x":-1.5761969999999934,"y":-0.8451341999999897},{"x":-1.5761969999999934,"y":-1.0011918000000009}]} />
<silkscreenpath route={[{"x":-1.5761969999999934,"y":1.001191800000015},{"x":-1.5761969999999934,"y":0.8451342000000039}]} />
<silkscreenpath route={[{"x":-1.5761969999999934,"y":1.001191800000015},{"x":1.5761969999999792,"y":1.001191800000015}]} />
<silkscreenpath route={[{"x":-1.5761969999999934,"y":-1.0011918000000009},{"x":1.5761969999999792,"y":-1.0011918000000009}]} />
<silkscreenpath route={[{"x":0.7913877999999954,"y":1.001191800000015},{"x":0.7913877999999954,"y":-1.0011918000000009}]} />
<silkscreentext text="{NAME}" pcbX="-0.0127mm" pcbY="2.0668mm" anchorAlignment="center" fontSize="1mm" />
<fabricationnotepath route={[{"x":-1.277997443999979,"y":-0.11099977799999294},{"x":-1.277997443999979,"y":0.11099977800000715},{"x":-0.3899992199999929,"y":0.11099977800000715},{"x":-1.277997443999979,"y":-0.11099977799999294}]} strokeWidth="0.254mm" />
<fabricationnotepath route={[{"x":1.2779974439999933,"y":-0.11099977799999294},{"x":1.2779974439999933,"y":0.11099977800000715},{"x":0.3899992200000071,"y":0.11099977800000715},{"x":1.2779974439999933,"y":-0.11099977799999294}]} strokeWidth="0.254mm" />
<fabricationnotepath route={[{"x":-0.944998109999986,"y":-0.7399985200000003},{"x":-0.944998109999986,"y":0.7399985200000145},{"x":-0.7229985540000001,"y":0.7399985200000145},{"x":-0.944998109999986,"y":-0.7399985200000003}]} strokeWidth="0.254mm" />
<courtyardoutline outline={[{"x":-2.4780753000000004,"y":1.1999854000000028},{"x":2.4780753000000004,"y":1.1999854000000028},{"x":2.4780753000000004,"y":-1.2000108000000012},{"x":-2.4780753000000004,"y":-1.2000108000000012},{"x":-2.4780753000000004,"y":1.1999854000000028}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 0,
        modelOriginPosition: { x: -0.000012700000013410317, y: 0.000012699999999199463, z: -0.16 },
      }}
      {...props}
    />
  )
}