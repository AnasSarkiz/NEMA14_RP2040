import objPath from "./EEEFPV101XAP.obj"
import stepPath from "./EEEFPV101XAP.step"
import type { CapacitorProps } from "@tscircuit/props"

export const EEEFPV101XAP = (props: Omit<CapacitorProps, "capacitance">) => {
  const { name = "C1", ...restProps } = props

  return (
    <capacitor
      name={name}
      capacitance="100uF"
      polarized
      supplierPartNumbers={{
  "jlcpcb": [
    "C178585"
  ]
}}
      manufacturerPartNumber="EEEFPV101XAP"
      footprint={<footprint>
        <smtpad portHints={["pin2"]} pcbX="2.670048mm" pcbY="0mm" width="3.499993mm" height="1.1999976mm" shape="rect" />
<smtpad portHints={["pin1"]} pcbX="-2.670048mm" pcbY="0mm" width="3.499993mm" height="1.1999976mm" shape="rect" />
<silkscreenpath route={[{"x":3.3555686000000833,"y":-0.7393177999999807},{"x":3.3756600000001526,"y":-3.375685400000066},{"x":-1.9812253999998575,"y":-3.375685400000066},{"x":-3.375685399999952,"y":-1.9812253999999712},{"x":-3.3623503999999684,"y":-0.6858000000000857}]} />
<silkscreenpath route={[{"x":3.369462399999975,"y":0.7076693999999861},{"x":3.376168000000007,"y":3.37614259999998},{"x":-1.9800315999999611,"y":3.37614259999998},{"x":-3.3761679999998933,"y":1.980006200000048},{"x":-3.3761679999998933,"y":0.6857745999999452}]} />
<silkscreentext text="{NAME}" pcbX="-0.001016mm" pcbY="4.38328mm" anchorAlignment="center" fontSize="1mm" />
<fabricationnotepath route={[{"x":-2.805023599999913,"y":0.6599681999999802},{"x":-2.805023599999913,"y":-0.6600190000000339},{"x":-2.60703060000003,"y":-0.6600190000000339},{"x":-2.60703060000003,"y":0.6599681999999802},{"x":-2.805023599999913,"y":0.6599681999999802}]} strokeWidth="0.254mm" />
<fabricationnotepath route={[{"x":-3.1020257999999785,"y":0.09898379999992812},{"x":-3.1020257999999785,"y":-0.09903460000009545},{"x":-2.310028399999851,"y":-0.09903460000009545},{"x":-2.310028399999851,"y":0.09898379999992812},{"x":-3.1020257999999785,"y":0.09898379999992812}]} strokeWidth="0.254mm" />
<fabricationnotepath route={[{"x":3.1019750000000386,"y":0.09898379999992812},{"x":3.1019750000000386,"y":-0.09903460000009545},{"x":2.309977599999911,"y":-0.09903460000009545},{"x":2.309977599999911,"y":0.09898379999992812},{"x":3.1019750000000386,"y":0.09898379999992812}]} strokeWidth="0.254mm" />
<courtyardoutline outline={[{"x":-4.670044499999904,"y":3.5500187999999753},{"x":4.670044499999904,"y":3.5500187999999753},{"x":4.670044499999904,"y":-3.5499680000000353},{"x":-4.670044499999904,"y":-3.5499680000000353},{"x":-4.670044499999904,"y":3.5500187999999753}]} />
      </footprint>}
      cadModel={{
        objUrl: objPath,
        stepUrl: stepPath,
        pcbRotationOffset: 180,
        modelOriginPosition: { x: 0.000038099999983387534, y: 0.00002539999979944696, z: -0.02 },
      }}
      {...restProps}
    />
  )
}