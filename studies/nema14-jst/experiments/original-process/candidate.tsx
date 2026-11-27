/** Original-hole comparison only. Accepted candidate and production source are unchanged. */
import React from 'react'
import Base from '../tolerance/candidate'
import paths from './paths.json'
import vias from './vias.json'
export default function Candidate({copper=true,routingDisabled=true,adapter,boardRef}:{copper?:boolean,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 const replacements=new Map((paths as any[]).map(p=>[p.name,p]));
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,name=e.props.name,p=replacements.get(name),v=(vias as Record<string,any>)[name];if(copper&&p)return <trace key={name} name={name} from={p.from} to={p.to} thickness={p.width_mm} pcbPathRelativeTo={p.anchor} pcbPaths={[p.local_points]}/>;return React.cloneElement(e,{...(v?{pcbX:v.x,pcbY:v.y,outerDiameter:.55,holeDiameter:.30}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(Base({copper,process:'locked',routingDisabled}));return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})})
}
