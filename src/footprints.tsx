import React from "react"
export const A4988Footprint = () => <footprint>
<smtpad portHints={["pin1"]} pcbX={-2.4} pcbY={1.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin2"]} pcbX={-2.4} pcbY={1} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin3"]} pcbX={-2.4} pcbY={0.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin4"]} pcbX={-2.4} pcbY={0} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin5"]} pcbX={-2.4} pcbY={-0.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin6"]} pcbX={-2.4} pcbY={-1} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin7"]} pcbX={-2.4} pcbY={-1.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin8"]} pcbX={-1.5} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin9"]} pcbX={-1} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin10"]} pcbX={-0.5} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin11"]} pcbX={0} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin12"]} pcbX={0.5} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin13"]} pcbX={1} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin14"]} pcbX={1.5} pcbY={-2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin15"]} pcbX={2.4} pcbY={-1.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin16"]} pcbX={2.4} pcbY={-1} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin17"]} pcbX={2.4} pcbY={-0.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin18"]} pcbX={2.4} pcbY={0} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin19"]} pcbX={2.4} pcbY={0.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin20"]} pcbX={2.4} pcbY={1} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin21"]} pcbX={2.4} pcbY={1.5} width={1.15} height={0.27} shape="rect" />
<smtpad portHints={["pin22"]} pcbX={1.5} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin23"]} pcbX={1} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin24"]} pcbX={0.5} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin25"]} pcbX={0} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin26"]} pcbX={-0.5} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin27"]} pcbX={-1} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin28"]} pcbX={-1.5} pcbY={2.4} width={0.27} height={1.15} shape="rect" />
<smtpad portHints={["pin29"]} pcbX={0} pcbY={0} width={3.15} height={3.15} shape="rect" />
<courtyardrect width={6.2} height={6.2} />
</footprint>
export const CH224Footprint = () => <footprint>
<smtpad portHints={["pin1"]} pcbX={-2.6375} pcbY={2} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin2"]} pcbX={-2.6375} pcbY={1} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin3"]} pcbX={-2.6375} pcbY={0} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin4"]} pcbX={-2.6375} pcbY={-1} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin5"]} pcbX={-2.6375} pcbY={-2} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin6"]} pcbX={2.6375} pcbY={-2} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin7"]} pcbX={2.6375} pcbY={-1} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin8"]} pcbX={2.6375} pcbY={0} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin9"]} pcbX={2.6375} pcbY={1} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin10"]} pcbX={2.6375} pcbY={2} width={1.675} height={.6} shape="rect" />
<smtpad portHints={["pin11"]} pcbX={0} pcbY={0} width={2.1} height={3.3} shape="rect" />
<courtyardrect width={7.45} height={5.4} />
</footprint>
export const EsdFootprint = () => <footprint>
{[[-1.1,.95],[-1.1,0],[-1.1,-.95],[1.1,-.95],[1.1,0],[1.1,.95]].map(([x,y],i)=><React.Fragment key={i}><smtpad portHints={[`pin${i+1}`]} pcbX={x} pcbY={y} width={1} height={.6} shape="rect" /></React.Fragment>)}
<courtyardrect width={3.5} height={3.4} />
</footprint>
export const BulkFootprint = () => <footprint>
<platedhole portHints={["pin1"]} pcbX={-1} pcbY={0} shape="circle" holeDiameter={.7} outerDiameter={1.4} />
<platedhole portHints={["pin2"]} pcbX={1} pcbY={0} shape="circle" holeDiameter={.7} outerDiameter={1.4} />
<silkscreencircle pcbX={0} pcbY={0} radius={2.5} strokeWidth={.12} />
<courtyardcircle radius={2.75} />
</footprint>
