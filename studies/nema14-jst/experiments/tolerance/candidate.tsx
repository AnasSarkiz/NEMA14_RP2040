import React from 'react'
import Base from '../reconnect/candidate'
import {type Process} from '../placement/candidate'
import poses from './poses.json'
import paths from './paths.json'
import vreg from './vreg.json'
export default function Candidate({copper=true,chargePump=true,process='locked',routingDisabled=true,adapter,boardRef}:{copper?:boolean,chargePump?:boolean,process?:Process,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 const replacement=new Map((paths as any[]).map(p=>[p.name,p]));
 function trace(p:any){return <trace key={p.name} name={p.name} from={p.from} to={p.to} thickness={p.width_mm} pcbPathRelativeTo={p.from} pcbPath={p.local_points}/>}
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,name=e.props.name;const q=(poses as Record<string,number[]>)[name];if(['AUTHORED_CP1_CORRIDOR','AUTHORED_CP2_CORRIDOR'].includes(name))return copper&&chargePump&&replacement.has(name)?trace(replacement.get(name)):null;return React.cloneElement(e,{...(q?{pcbX:q[0],pcbY:q[1],pcbRotation:q[2]}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({copper,process,routingDisabled}));return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})},[root.props.children,...(copper?[trace(vreg)]:[])])
}
