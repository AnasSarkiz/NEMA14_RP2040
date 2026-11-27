/** Minimal pinned EP overlap controls. No allow-via-in-pad flag or process adoption. */
import React from 'react'
export type Mode='own'|'own-exposed'|'foreign'|'outside'|'no-vias'
export default function EpControl({mode='own'}:{mode?:Mode}={}){const xs=mode==='outside'?[-2.4,2.4]:[-.5,.5];return <board width={35} height={35} layers={4} thickness={1.6} routingDisabled>
 <net name="GND"/><net name="OTHER"/>
 <chip name="U_EP" pinLabels={{pin1:['GND']}} footprint={<footprint><smtpad portHints={['pin1']} shape="rect" width={3.15} height={3.15}/></footprint>}/>
 <trace from=".U_EP > .GND" to="net.GND"/>
 {mode!=='no-vias'&&xs.flatMap(x=>[-.5,.5].map(y=><via {...({key:x+','+y} as any)} name={'TV_'+x+'_'+y} pcbX={x} pcbY={y} holeDiameter={.30} outerDiameter={.75} layers={['top','inner1','inner2','bottom']} tented={mode==='own-exposed'?'exposed':'bottom_tented'} connectsTo={mode==='foreign'?'net.OTHER':'net.GND'}/>))}
 </board>}
