/** Separate full placement candidate. Production source and physical pin contract are inherited unchanged. */
import React from 'react'
import {Via,Port} from '@tscircuit/core'
import Base from '../anchored/fixture'
import poses from './poses.json'
import moved from './moved-names.json'
import spec from './generated.json'
import cp1 from './cp1-path.json'
function bind(v:Via|null){if(!v)return;for(const layer of ['inner1','inner2'] as const){if(v.children.some((p:any)=>p.props?.name===layer))continue;const p=new Port({name:layer,layer});p.registerMatch(v);v.add(p)}}
export type Process='locked'|'small-hole-screen'
export default function Candidate({copper=true,cp1Enabled=true,process='locked',routingDisabled=true,adapter,boardRef}:{copper?:boolean,cp1Enabled?:boolean,process?:Process,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 const small=process==='small-hole-screen'
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,name=e.props.name,q=moved.includes(name)?(poses as Record<string,number[]>)[name]:undefined;if(copper&&(spec.paths as any)[name])return null;return React.cloneElement(e,{...(q?{pcbX:q[0],pcbY:q[1],pcbRotation:q[2]}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({scope:'board',copper:false,routingDisabled,smallStar:small}));const compact=['V_STAR_A','V_STAR_B','V_GB','V_KBN_S'];const extra=copper?[...spec.fragments.map((r:any)=><trace key={r.name} name={r.name} from={r.from} to={r.to} thickness={r.width_mm} pcbPathRelativeTo={r.anchor} {...(r.representation==='singular'?{pcbPath:r.path}:{pcbPaths:r.paths})}/>),...spec.vias.map((v:any)=><via {...({key:v.name,ref:bind} as any)} name={v.name} pcbX={v.x} pcbY={v.y} fromLayer="top" toLayer="bottom" outerDiameter={compact.includes(v.name)?.45:.55} holeDiameter={small&&compact.includes(v.name)?.2:.3} connectsTo={'net.'+v.net}/>),...(cp1Enabled&&(cp1 as any).enabled?[<trace key="AUTHORED_CP1_CORRIDOR" name="AUTHORED_CP1_CORRIDOR" from=".U_DRV > .CP1" to=".C_CP > .pin1" thickness={.16} pcbPathRelativeTo=".U_DRV > .CP1" pcbPath={(cp1 as any).local_points}/>]:[])]:[]
 return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})},[root.props.children,...extra])
}
