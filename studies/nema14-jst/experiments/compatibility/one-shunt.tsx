/** Same physical shunt and amplifier on both pinned native stacks. */
import React from 'react'
import {ERJL06KF50MV} from '../../imports/supplier/ERJL06KF50MV/ERJL06KF50MV'
import {INA240A1PWR} from '../../imports/supplier/INA240A1PWR/INA240A1PWR'
const inner=.999998-1.1325352/2,outer=.999998+1.1325352/2
export default function OneShunt({authored=true}:{authored?:boolean}={}){return <board width={20} height={18} layers={4} thickness={1.6} minTraceWidth={.16} minTraceToPadEdgeClearance={.15} minPadEdgeToPadEdgeClearance={.15} minViaHoleDiameter={.3} minViaPadDiameter={.45} minBoardEdgeClearance={.25} autorouter={{local:true,traceClearance:.15}} autorouterEffortLevel="2x" schAutoLayoutEnabled={false}>
<net name="GND" isGroundNet/><net name="V3V3" isPowerNet/>
<ERJL06KF50MV name="R_SHUNT_A" pcbX={0} pcbY={-2}/>
<INA240A1PWR name="U_IA" pcbX={0} pcbY={4} noConnect={['NC','OUT']} connections={{GND:'net.GND',REF1:'net.GND',REF2:'net.GND',VS:'net.V3V3'}}/>
{(['POS','NEG'] as const).map((pole,k)=>{const s=k?1:-1,pin=k?'pin2':'pin1';return <React.Fragment key={pole}>
<testpoint name={'P_A_'+pole} pcbX={s*4} pcbY={-2} footprint={<footprint><smtpad portHints={['pin1']} shape="rect" width={.8} height={.8}/></footprint>}/>
<trace name={'KELVIN_A_'+pole} from={'.R_SHUNT_A > .'+pin} to={'.U_IA > .IN_'+pole} thickness={.16} {...(authored?{pcbPath:[{x:s*inner,y:0},{x:s*inner,y:1.5}]}:{})}/>
<trace name={'POWER_A_'+pole} from={'.R_SHUNT_A > .'+pin} to={'.P_A_'+pole+' > .pin1'} thickness={.45} {...(authored?{pcbPath:[{x:s*outer,y:0},{x:s*3,y:0}]}:{})}/>
</React.Fragment>})}
<testpoint name="P_VCC" pcbX={4} pcbY={7} footprint={<footprint><smtpad portHints={["pin1"]} shape="rect" width={.8} height={.8}/></footprint>}/><trace name="VCC_SOURCE" from=".P_VCC > .pin1" to="net.V3V3" thickness={.16}/></board>}
