/** Separate full controller candidate. Accepted production placement is unchanged. */
import React from 'react'
import Board from '../../src/board'
import authored from './authored-paths.json'
const paths=new Map(authored.map(p=>[p.name,p]))
function visit(node:any):any {
 if(!React.isValidElement(node))return node
 const e=node as React.ReactElement<any>,p=paths.get(e.props.name);const props:any={}
 if(p){props.pcbPathRelativeTo=p.anchor;if(p.name.startsWith('KELVIN'))props.pcbPath=p.pcbPaths[0].slice(1,-1);else props.pcbPaths=p.pcbPaths}
 if(e.props.children!==undefined)props.children=React.Children.map(e.props.children,n=>visit(n))
 return React.cloneElement(e,props)
}
export default function Candidate({routingDisabled=false}:{routingDisabled?:boolean}={}){
 const root:any=visit(Board({routingDisabled}))
 return React.cloneElement(root,{pcbStyle:{viaPadDiameter:.45,viaHoleDiameter:.3}})
}
