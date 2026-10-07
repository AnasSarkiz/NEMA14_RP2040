import React from "react"
import { type ChipProps } from "tscircuit"
export const USB = (props: ChipProps) => (
  <chip
    footprint={<footprint>
        <hole pcbX="2.89mm" pcbY="2.6mm" diameter="0.65mm" />
<hole pcbX="-2.89mm" pcbY="2.6mm" diameter="0.65mm" />
<platedhole  portHints={["pin13"]} pcbX="4.32mm" pcbY="-1.05mm" outerHeight="1.6mm" outerWidth="1mm" holeHeight="1.2mm" holeWidth="0.6mm" shape="pill" pcbRotation="0deg" />
<platedhole  portHints={["pin13"]} pcbX="-4.32mm" pcbY="-1.05mm" outerHeight="1.6mm" outerWidth="1mm" holeHeight="1.2mm" holeWidth="0.6mm" shape="pill" pcbRotation="0deg" />
<platedhole  portHints={["pin13"]} pcbX="-4.32mm" pcbY="3.13mm" outerHeight="2.1mm" outerWidth="1mm" holeHeight="1.7mm" holeWidth="0.6mm" shape="pill" pcbRotation="0deg" />
<platedhole  portHints={["pin13"]} pcbX="4.32mm" pcbY="3.13mm" outerHeight="2.1mm" outerWidth="1mm" holeHeight="1.7mm" holeWidth="0.6mm" shape="pill" pcbRotation="0deg" />
<smtpad portHints={["pin7"]} pcbX="-0.25mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin6"]} pcbX="1.75mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin11"]} pcbX="1.25mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin8"]} pcbX="0.75mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin9"]} pcbX="0.25mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin10"]} pcbX="-0.75mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin5"]} pcbX="-1.25mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin12"]} pcbX="-1.75mm" pcbY="4.045mm" layer="top" width="0.3mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin2"]} pcbX="3.25mm" pcbY="4.045mm" layer="top" width="0.6mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin4"]} pcbX="2.45mm" pcbY="4.045mm" layer="top" width="0.6mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin3"]} pcbX="-2.45mm" pcbY="4.045mm" layer="top" width="0.6mm" height="1.45mm" shape="rect" />
<smtpad portHints={["pin1"]} pcbX="-3.25mm" pcbY="4.045mm" layer="top" width="0.6mm" height="1.45mm" shape="rect" />
<silkscreenpath route={[{"x":-4.7,"y":-2},{"x":-4.7,"y":-3.9}]} strokeWidth={0.12} />
<silkscreenpath route={[{"x":-4.7,"y":1.9},{"x":-4.7,"y":-0.1}]} strokeWidth={0.12} />
<silkscreenpath route={[{"x":4.7,"y":-2},{"x":4.7,"y":-3.9}]} strokeWidth={0.12} />
<silkscreenpath route={[{"x":4.7,"y":1.9},{"x":4.7,"y":-0.1}]} strokeWidth={0.12} />
<silkscreenpath route={[{"x":-4.7,"y":-3.9},{"x":4.7,"y":-3.9}]} strokeWidth={0.12} />
<fabricationnotepath route={[{"x":4.47,"y":3.65},{"x":4.47,"y":-3.65}]} strokeWidth={0.1} />
<fabricationnotepath route={[{"x":-4.47,"y":-3.65},{"x":4.47,"y":-3.65}]} strokeWidth={0.1} />
<fabricationnotepath route={[{"x":-4.47,"y":3.65},{"x":-4.47,"y":-3.65}]} strokeWidth={0.1} />
<fabricationnotepath route={[{"x":-4.47,"y":3.65},{"x":4.47,"y":3.65}]} strokeWidth={0.1} />
<courtyardrect width={10.64} height={9.42} pcbY={0.56} />
      </footprint>}
    {...props}
  />
)