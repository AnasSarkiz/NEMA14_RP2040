/** Isolated pinned endpoint semantic diagnostic; no external return or new process. */
import React from 'react'
export default function Endpoint({inside=false}:{inside?:boolean}={}){return <board width={35} height={35} layers={4} routingDisabled>
 <chip name="U_TEST" pcbX={7.600127} pcbY={7.449873} pinLabels={{pin1:['GND']}} footprint={<footprint><smtpad portHints={['pin1']} shape="rect" width={3.1999936} height={3.1999936}/></footprint>}/>
 {[['A',5.30,7.449873,5.84,6.01],['B',9.90,6.949493,9.36,9.19]].map(([n,x,y,old,corrected]:any)=><React.Fragment key={n}><chip name={'T'+n} pcbX={x} pcbY={y} pinLabels={{pin1:['GND']}} footprint={<footprint><smtpad portHints={['pin1']} shape="circle" radius={.14}/></footprint>}/><trace name={'ENDPOINT_'+n} from=".U_TEST > .GND" to={'.T'+n+' > .GND'} thickness={.6} pcbPathRelativeTo=".U_TEST > .GND" pcbPaths={[[ {x:(inside?corrected:old)-7.600127,y:y-7.449873},{x:x-7.600127,y:y-7.449873}]]}/></React.Fragment>)}
 </board>}
