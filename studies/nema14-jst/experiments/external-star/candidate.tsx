/** Rejected-control study only: full controller with external star-via escapes, supplier pads exact. */
import React from 'react'
import Base from '../vreg-star/candidate'
import paths from './paths.json'
import vias from './vias.json'
export default function Candidate({routingDisabled=true,adapter,boardRef}:{routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 const replacement=new Map((paths as any[]).map(p=>[p.name,p]));function trace(p:any){return <trace key={p.name} name={p.name} from={p.from} to={p.to} thickness={p.width_mm} pcbPathRelativeTo={p.anchor} pcbPaths={[p.local_points]}/>}
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,n=e.props.name,p=replacement.get(n),v=(vias as Record<string,any>)[n];if(p)return trace(p);return React.cloneElement(e,{...(v?{pcbX:v.x,pcbY:v.y}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({routingDisabled}));return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})},[root.props.children,...(paths as any[]).filter(p=>p.name.endsWith('_EXTERNAL')).map(trace)])
}
