/** Focused CP2/buzzer comparison; the accepted controller and comparison baseline are untouched. */
import React from 'react'
import {Via,Port} from '@tscircuit/core'
import vias from './vias.json'
function bind(v:Via|null){if(!v)return;for(const layer of ['inner1','inner2'] as const){if(v.children.some((p:any)=>p.props?.name===layer))continue;const p=new Port({name:layer,layer});p.registerMatch(v);v.add(p)}}
import Base,{type Process} from '../placement/candidate'
import poses from './poses.json'
import paths from './paths.json'
export default function Candidate({copper=true,extra=true,process='locked',routingDisabled=true,adapter,boardRef}:{copper?:boolean,extra?:boolean,process?:Process,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>;if(e.props.name==='AUTHORED_CP1_CORRIDOR')return null;const q=(poses as Record<string,number[]>)[e.props.name];return React.cloneElement(e,{...(q?{pcbX:q[0],pcbY:q[1],pcbRotation:q[2]}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({copper,process,routingDisabled}));const add=copper&&extra?(paths as any[]).map(p=><trace key={p.name} name={p.name} from={p.from} to={p.to} thickness={p.width_mm} pcbPathRelativeTo={p.from} pcbPath={p.local_points}/>):[]
 return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})},[root.props.children,...(copper?vias.map(v=><via {...({key:v.name,ref:bind} as any)} name={v.name} pcbX={v.x} pcbY={v.y} fromLayer="top" toLayer="bottom" holeDiameter={v.hole_mm} outerDiameter={v.pad_mm} connectsTo={'net.'+v.net}/>):[]),...add])
}
