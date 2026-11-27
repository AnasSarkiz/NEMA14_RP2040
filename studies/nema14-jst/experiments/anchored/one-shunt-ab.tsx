/** Native singular/plural same-geometry crossing reproducer for the existing upstream issue. */
import React from 'react'
import OneShunt from '../compatibility/one-shunt'
export default function AB({plural=false,routingDisabled=false,adapter,boardRef}:{plural?:boolean,routingDisabled?:boolean,adapter?:any,boardRef?:any}={}){
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>;if(plural&&e.props.pcbPath)return React.cloneElement(e,{pcbPath:undefined,pcbPaths:[[e.props.from,...e.props.pcbPath,e.props.to]]});return React.cloneElement(e,{...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(OneShunt());return React.cloneElement(root,{routingDisabled,...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{})},[root.props.children,...[-5,1].map((y,i)=><testpoint key={'CROSS'+i} name={'CROSS'+i} pcbX={-2.5} pcbY={y} footprint={<footprint><smtpad portHints={['pin1']} shape="rect" width={.6} height={.6}/></footprint>}/>),<trace key="CROSS" name="CROSS" from=".CROSS0 > .pin1" to=".CROSS1 > .pin1" thickness={.16}/>])
}
