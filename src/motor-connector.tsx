import React from "react"
import type { ChipProps } from "@tscircuit/props"

// JST PH manufacturer drawing, mounting-side view: 2.00 +/-0.05 mm
// non-accumulating pitch; 0.7 +0.1/-0 mm finished bores. The stock C131334
// import has 1 mm bores and a different anchor. Preserve it as evidence;
// this explicit manufacturer-derived land pattern is the assembly authority.
export function MotorConnector(props: ChipProps) {
  return <chip {...props} manufacturerPartNumber="B4B-PH-K-S(LF)(SN)"
    supplierPartNumbers={{jlcpcb:["C131334"]}}
    footprint={<footprint insertionDirection="from_above">
      {[-3,-1,1,3].map((x,i)=><React.Fragment key={i}><platedhole portHints={[`pin${i+1}`]}
        pcbX={x} pcbY={0} shape="circle" holeDiameter={0.75} outerDiameter={1.6} /></React.Fragment>)}
      <courtyardrect width={10.4} height={5.2} pcbY={-0.65} />
      <silkscreencircle pcbX={-4.4} pcbY={0} radius={0.25} strokeWidth={0.12}/>
    </footprint>}
    cadModel={{
      objUrl:"https://modelcdn.tscircuit.com/easyeda_models/assets/C131334.obj?uuid=3b95b8b4d5d24ff4a871a43c952e432a",
      stepUrl:"https://modelcdn.tscircuit.com/easyeda_models/assets/C131334.step?uuid=3b95b8b4d5d24ff4a871a43c952e432a",
      modelOriginPosition:{x:3,y:0,z:0}, pcbRotationOffset:0,
    }}/>
}
