import React from 'react'
import {ERJL06KF50MV} from '../../imports/supplier/ERJL06KF50MV/ERJL06KF50MV'
import {INA240A1PWR} from '../../imports/supplier/INA240A1PWR/INA240A1PWR'
const inner=.999998-1.1325352/2, outer=.999998+1.1325352/2
export default ()=><board width={35} height={35} layers={4} thickness={1.6} minTraceWidth={.16} minTraceToPadEdgeClearance={.15} minPadEdgeToPadEdgeClearance={.15} minViaHoleDiameter={.3} minViaPadDiameter={.45} minViaHoleEdgeToViaHoleEdgeClearance={.2} minPlatedHoleDrillEdgeToDrillEdgeClearance={.45} minBoardEdgeClearance={.25} autorouter={{local:true,traceClearance:.15}} autorouterEffortLevel="2x" schAutoLayoutEnabled={false}>
{[-13,13].flatMap(x=>[-13,13].map(y=><React.Fragment key={`${x},${y}`}><hole pcbX={x} pcbY={y} diameter={3.2}/><keepout shape="circle" pcbX={x} pcbY={y} radius={3.2} layers={['top','inner1','inner2','bottom']} allowPlacements={false}/></React.Fragment>))}
<net name="GND" isGroundNet/><net name="V3V3" isPowerNet/>
{(['A','B'] as const).map((phase,i)=>{const x=i?5:-5;return <React.Fragment key={phase}>
<ERJL06KF50MV name={'R_SHUNT_'+phase} pcbX={x} pcbY={0}/>
<INA240A1PWR name={'U_I'+phase} pcbX={x} pcbY={6} noConnect={['NC','OUT']} connections={{GND:'net.GND',REF1:'net.GND',REF2:'net.GND',VS:'net.V3V3'}}/>
{(['POS','NEG'] as const).map((pole,k)=>{const s=k?1:-1,pin=k?'pin2':'pin1';return <React.Fragment key={pole}>
<testpoint name={'P_'+phase+'_'+pole} pcbX={x+s*4} pcbY={0} footprint={<footprint><smtpad portHints={['pin1']} shape="rect" width={.8} height={.8}/></footprint>}/>
<trace name={'KELVIN_'+phase+'_'+pole} from={'.R_SHUNT_'+phase+' > .'+pin} to={'.U_I'+phase+' > .IN_'+pole} thickness={.16} pcbPath={[{x:s*inner,y:0},{x:s*inner,y:1.5}]}/>
<trace name={'POWER_'+phase+'_'+pole} from={'.R_SHUNT_'+phase+' > .'+pin} to={'.P_'+phase+'_'+pole+' > .pin1'} thickness={.45} pcbPath={[{x:s*outer,y:0},{x:s*3,y:0}]}/>
</React.Fragment>})}
</React.Fragment>})}
</board>
