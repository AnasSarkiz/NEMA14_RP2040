/** Isolated compact diagnostic. Full-board promotion requires every gate. */
import React from 'react'
import Board from '../../src/board'
import ThroughVia from '../reachability/through-via'
import poses from './candidate-poses.json'
import names from './source-names.json'
import scopeNames from './scope.json'
import authored from './authored.json'
function visit(node:any,scope:boolean,copper:boolean):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,name=e.props.name,p=(poses as Record<string,number[]>)[name];if(scope&&names.includes(name)&&!scopeNames.includes(name))return null;const route:any=(authored.paths as any)[name];return React.cloneElement(e,{...(p?{pcbX:p[0],pcbY:p[1],pcbRotation:p[2]}:{}),...(copper&&route?{pcbPathRelativeTo:route.anchor,pcbPaths:route.paths}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,n=>visit(n,scope,copper))}:{})})}
export default function Candidate({routingDisabled=false,scope=false,copper=true}:{routingDisabled?:boolean,scope?:boolean,copper?:boolean}={}){
 const root:any=visit(Board({routingDisabled}),scope,copper)
 const extra=copper?[...authored.vias.map((v:any)=><ThroughVia key={v.name} name={v.name} x={v.x} y={v.y} net={v.net}/>),...authored.returns.map((p:any)=><trace key={p.name} name={p.name} from={p.from} to={p.to} thickness={.6} pcbPaths={p.paths}/>)]:[]
 return React.cloneElement(root,{pcbStyle:{viaPadDiameter:.45,viaHoleDiameter:.3}},[root.props.children,...extra])
}
