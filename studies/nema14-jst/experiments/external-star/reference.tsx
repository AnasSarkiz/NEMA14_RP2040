/** Official A4988 ET page19 reference dimensions only; NOT supplier/tooling/assembly approval. */
import React from 'react'
import pads from './reference-pads.json'
export default function Reference(){return <board width={35} height={35} layers={4} thickness={1.6} routingDisabled><chip name="REFERENCE_DRIVER" manufacturerPartNumber="A4988SETTR-T" pinLabels={Object.fromEntries(pads.map(p=>['pin'+p.pin,p.pin===29?'EP':'P'+p.pin]))} footprint={<footprint>{pads.map(p=><smtpad {...({key:p.pin} as any)} portHints={['pin'+p.pin]} pcbX={p.x} pcbY={p.y} width={p.width} height={p.height} shape="rect"/>)}</footprint>}/></board>}
