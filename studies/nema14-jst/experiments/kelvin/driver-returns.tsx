import React from 'react'
import Board from './two-cap'
import {driverAdapter} from './driver-native-adapter'
// Isolated comparison with all vias outside actual pad copper. No production gate is waived.
export default function ReturnComparison(){
 const base:any=Board({routingDisabled:false});
 const returns=[{name:'R_SA',x:9.12,y:8.72,target:[10.9511238,3.7]},{name:'R_SB',x:7.2,y:8.72,target:[7.4488762,4.200887]}].map(q=>{const dx=q.target[0]-q.x,dy=q.target[1]-q.y;const target={x:dy,y:-dx};const source={x:.999998-1.1325352/2-.151,y:0};return <trace key={q.name} name={'AUTHORED_RETURN_'+q.name} from={'.'+q.name+' > .pin2'} to=".U_DRV > .EP" thickness={.6} pcbPath={[source,{...source,via:true,toLayer:'inner1'},source,target,{...target,via:true,fromLayer:'inner1',toLayer:'top'},target]}/>})
 return React.cloneElement(base,{autorouter:{algorithmFn:async(input:any)=>driverAdapter(input)},pcbStyle:{viaPadDiameter:.45,viaHoleDiameter:.3}},[base.props.children,...returns])
}
