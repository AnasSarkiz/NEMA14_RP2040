import React from 'react'
import {Via,Port} from '@tscircuit/core'
/** On this pinned Core, Via is constructed before it knows the four-layer parent.
 * Add the missing inner ports to the existing physical barrel before rendering.
 * No copper, hole, layer span or rule is changed by this port registration. */
function bindInnerPorts(via:Via|null){
 if(!via)return
 for(const layer of ['inner1','inner2'] as const){
  if(via.children.some((c:any)=>c.props?.name===layer))continue
  const port=new Port({name:layer,layer});port.registerMatch(via);via.add(port)
 }
}
export default function ThroughVia({name,x,y,net="GND"}:{name:string,x:number,y:number,net?:string}){
 return React.createElement('via' as any,{name,pcbX:x,pcbY:y,fromLayer:'top',toLayer:'bottom',outerDiameter:.45,holeDiameter:.3,connectsTo:'net.'+net,ref:bindInnerPorts})
}
