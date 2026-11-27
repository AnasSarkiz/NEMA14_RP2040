/** Separate capacitor/escape comparison; unchanged driver land pattern and original drills. */
import React from 'react'
import Base from '../original-process/candidate'
import poses from './poses.json'
import path from './path.json'
export default function Candidate({copper=true,vreg=true,routingDisabled=true,adapter,boardRef}:{copper?:boolean,vreg?:boolean,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,n=e.props.name,q=(poses as Record<string,number[]>)[n];if(n==='AUTHORED_VREG_BASELINE')return copper&&vreg?<trace name={path.name} from={path.from} to={path.to} thickness={path.width_mm} pcbPathRelativeTo={path.anchor} pcbPaths={[path.local_points]}/>:null;return React.cloneElement(e,{...(q?{pcbX:q[0],pcbY:q[1],pcbRotation:q[2]}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({copper,routingDisabled}));return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})})
}
