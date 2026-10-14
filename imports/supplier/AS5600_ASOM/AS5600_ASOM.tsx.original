import objPath from "./AS5600_ASOM.obj"
import stepPath from "./AS5600_ASOM.step"
import type { ChipProps } from "@tscircuit/props"

const pinLabels = {
  pin1: ["VDD5V"],
  pin2: ["VDD3V3"],
  pin3: ["OUT"],
  pin4: ["GND"],
  pin5: ["PGO"],
  pin6: ["SDA"],
  pin7: ["SCL"],
  pin8: ["DIR"]
} as const

const pinAttributes = {
  pin4: {requiresGround: true, mustBeConnected: true},
  pin1: {requiresPower: true, mustBeConnected: true, shouldHaveDecouplingCapacitor: true},
  pin2: {requiresPower: true, shouldHaveDecouplingCapacitor: true},
  pin3: {isOutput: true},
  pin8: {isInput: true},
  pin7: {isInput: true, capabilities: ["i2c_scl"]},
  pin6: {isInput: true, isOutput: true, isBidirectional: true, capabilities: ["i2c_sda"], canUseOpenDrain: true},
  pin5: {isInput: true, canUseInternalPullup: true}
} satisfies NonNullable<ChipProps["pinAttributes"]>

export const AS5600_ASOM = (props: ChipProps<typeof pinLabels>) => {
  return (
    <chip
      pinLabels={pinLabels}
      pinAttributes={pinAttributes}
      supplierPartNumbers={{
  "jlcpcb": [
    "C79815"
  ]
}}
      manufacturerPartNumber="AS5600-ASOM"
      footprint={<footprint>
        <smtpad portHints={["pin1"]} pcbX="-1.905mm" pcbY="-2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin2"]} pcbX="-0.635mm" pcbY="-2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin3"]} pcbX="0.635mm" pcbY="-2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin4"]} pcbX="1.905mm" pcbY="-2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin8"]} pcbX="-1.905mm" pcbY="2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin7"]} pcbX="-0.635mm" pcbY="2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin6"]} pcbX="0.635mm" pcbY="2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<smtpad portHints={["pin5"]} pcbX="1.905mm" pcbY="2.7051mm" width="0.5684012mm" height="1.950212mm" radius="0.2842006mm" shape="pill" />
<silkscreenpath route={[{"x":-2.4999950000001263,"y":-1.4999970000000076},{"x":2.499994999999899,"y":-1.4999970000000076}]} />
<silkscreenpath route={[{"x":-2.4999950000001263,"y":1.4999969999998939},{"x":2.499994999999899,"y":1.4999969999998939}]} />
<silkscreenpath route={[{"x":-2.4999950000001263,"y":-1.4999970000000076},{"x":-2.4999950000001263,"y":-0.7265669999998181}]} />
<silkscreenpath route={[{"x":-2.4999950000001263,"y":1.4999969999998939},{"x":-2.4999950000001263,"y":0.7262875999999778}]} />
<silkscreenpath route={[{"x":2.499994999999899,"y":1.4999969999998939},{"x":2.499994999999899,"y":-1.4999970000000076}]} />
<silkscreenpath route={[{"x":-2.4999950000001263,"y":-0.7265669999998181},{"x":-2.2625565730616017,"y":-0.6727720384950544},{"x":-2.056152369867391,"y":-0.5436666188794561},{"x":-1.9038872877111999,"y":-0.3537028085727343},{"x":-1.822805887847835,"y":-0.12414516642888884},{"x":-1.8219844264158382,"y":0.11930961309167287},{"x":-1.9015148578508843,"y":0.34940918924542075},{"x":-2.0524945415012326,"y":0.5403962034508822},{"x":-2.25802280368805,"y":0.6708915593560505},{"x":-2.495092800000066,"y":0.7262876000000915}]} />
<silkscreencircle pcbX="-1.778mm" pcbY="-1.016mm" radius="0.150114mm" />
<silkscreentext text="{NAME}" pcbX="0.0127mm" pcbY="4.4036mm" anchorAlignment="center" fontSize="1mm" />
<courtyardoutline outline={[{"x":-2.700007800000094,"y":3.9302059999999983},{"x":2.6999823999999535,"y":3.9302059999999983},{"x":2.6999823999999535,"y":-3.9302059999999983},{"x":-2.700007800000094,"y":-3.9302059999999983},{"x":-2.700007800000094,"y":3.9302059999999983}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 0,
        modelOriginPosition: { x: 0.000012700000070253736, y: 0, z: 0 },
      }}
      {...props}
    />
  )
}