/** DIGITAL REVIEW COUPON ONLY. Unqualified EP via process, not an accepted board. */
import React from 'react'
import pads from '../external-star/reference-pads.json'
export default function Candidate(){return <board width={35} height={35} layers={4} thickness={1.6} routingDisabled>
 <net name="GND"/>
 <chip name="D" manufacturerPartNumber="A4988SETTR-T" pinLabels={Object.fromEntries(pads.map(p=>['pin'+p.pin,[p.pin===29?'EP':'P'+p.pin]]))} footprint={<footprint>
  {pads.map(p=><smtpad {...({key:p.pin} as any)} portHints={['pin'+p.pin]} pcbX={p.x} pcbY={p.y} width={p.width} height={p.height} shape="rect" {...(p.pin===29?{solderPasteMargin:-2}:{})}/>)}
 </footprint>}/>
 {['EP','P3','P18'].map(p=><trace key={p} from={'.D > .'+p} to="net.GND"/>)}
 {[-.5,.5].flatMap(x=>[-.5,.5].map(y=><via {...({key:x+','+y} as any)} name={'EP_'+x+'_'+y} pcbX={x} pcbY={y} holeDiameter={.30} outerDiameter={.75} layers={['top','inner1','inner2','bottom']} tented="bottom_tented" connectsTo="net.GND"/>))}
 </board>}
