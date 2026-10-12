import objPath from "./DTC114EU3HZGT106.obj"
import stepPath from "./DTC114EU3HZGT106.step"
import type { ChipProps } from "@tscircuit/props"

const pinLabels = {
  pin1: ["E"],
  pin2: ["B"],
  pin3: ["C"]
} as const

export const DTC114EU3HZGT106 = (props: ChipProps<typeof pinLabels>) => {
  return (
    <chip
      pinLabels={pinLabels}
      symbol={
        <symbol>
          <port name="pin3" pinNumber={3} aliases={["C"]} direction="up" schX={0.2} schY={0.8} schStemLength={0.4} />
          <port name="pin1" pinNumber={1} aliases={["E"]} direction="down" schX={0.2} schY={-0.8} schStemLength={0.4} />
          <port name="pin2" pinNumber={2} aliases={["B"]} direction="left" schX={-1} schY={0} schStemLength={0.4} />
          <schematicpath points={[{"x":-0.6,"y":0},{"x":-0.52,"y":0},{"x":-0.5,"y":0.06},{"x":-0.46,"y":-0.06},{"x":-0.42,"y":0.06},{"x":-0.38,"y":-0.06},{"x":-0.34,"y":0.06},{"x":-0.3,"y":-0.06},{"x":-0.28,"y":0},{"x":-0.2,"y":0},{"x":0,"y":0}]} strokeColor="#880000" />
          <schematicpath points={[{"x":0,"y":0.18},{"x":0,"y":-0.18}]} strokeColor="#880000" />
          <schematicpath points={[{"x":0,"y":-0.06},{"x":0.2,"y":-0.2},{"x":0.2,"y":-0.4},{"x":-0.2,"y":-0.4},{"x":-0.2,"y":-0.32},{"x":-0.26,"y":-0.3},{"x":-0.14,"y":-0.26},{"x":-0.26,"y":-0.22},{"x":-0.14,"y":-0.18},{"x":-0.26,"y":-0.14},{"x":-0.14,"y":-0.1},{"x":-0.2,"y":-0.08},{"x":-0.2,"y":0}]} strokeColor="#880000" />
          <schematicpath points={[{"x":0.2,"y":0.4},{"x":0.2,"y":0.2},{"x":0,"y":0.06}]} strokeColor="#880000" />
          <schematicpath points={[{"x":0.2,"y":-0.2},{"x":0.08,"y":-0.18},{"x":0.14,"y":-0.1},{"x":0.2,"y":-0.2}]} strokeColor="#880000" isFilled fillColor="#880000" />
          <schematictext schX={-0.401} schY={1.022} text="{NAME}" fontSize={0.2} anchor="bottom_center" />
        </symbol>
      }
      supplierPartNumbers={{
  "jlcpcb": [
    "C509876"
  ]
}}
      manufacturerPartNumber="DTC114EU3HZGT106"
      footprint={<footprint>
        <smtpad portHints={["pin3"]} pcbX="-0.94996mm" pcbY="0mm" width="0.8999982mm" height="0.6999986mm" shape="rect" />
<smtpad portHints={["pin1"]} pcbX="0.94996mm" pcbY="0.649986mm" width="0.8999982mm" height="0.6999986mm" shape="rect" />
<smtpad portHints={["pin2"]} pcbX="0.94996mm" pcbY="-0.649986mm" width="0.8999982mm" height="0.6999986mm" shape="rect" />
<silkscreenpath route={[{"x":-0.6999985999999581,"y":1.1999975999999606},{"x":0.6999731999999312,"y":1.1999975999999606}]} />
<silkscreenpath route={[{"x":-0.6999985999999581,"y":-1.1999722000000475},{"x":-0.6999985999999581,"y":-0.5041391999999405}]} />
<silkscreenpath route={[{"x":-0.6999985999999581,"y":0.5041645999999673},{"x":-0.6999985999999581,"y":1.1937999999998965}]} />
<silkscreenpath route={[{"x":-0.6999985999999581,"y":-1.1999722000000475},{"x":0.6802119999999832,"y":-1.1999722000000475}]} />
<silkscreenpath route={[{"x":0.6999731999999312,"y":1.1999975999999606},{"x":0.6999731999999312,"y":1.154125199999953}]} />
<silkscreenpath route={[{"x":0.6999731999999312,"y":0.1458214000000453},{"x":0.6999731999999312,"y":-0.14584679999995842}]} />
<silkscreenpath route={[{"x":0.6999731999999312,"y":-1.15415059999998},{"x":0.6999731999999312,"y":-1.1999722000000475}]} />
<silkscreentext text="{NAME}" pcbX="0.065532mm" pcbY="2.7526mm" anchorAlignment="center" fontSize="1mm" />
<courtyardoutline outline={[{"x":-1.6499590999999327,"y":1.2499979999998914},{"x":1.6499590999999327,"y":1.2499979999998914},{"x":1.6499590999999327,"y":-1.2499979999998914},{"x":-1.6499590999999327,"y":-1.2499979999998914},{"x":-1.6499590999999327,"y":1.2499979999998914}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 180,
        modelOriginPosition: { x: 0.000012699999956566899, y: 0, z: -0.1 },
      }}
      {...props}
    />
  )
}