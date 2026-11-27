/** Reversible comparison only. Two bottom capacitors are not adopted in controller.tsx. */
import React from 'react'
import Board from '../../src/board'
import delta from './two-cap-placement.json'
function apply(node:any):any {
 if(!React.isValidElement(node))return node
 const e=node as React.ReactElement<any>;const override=(delta as Record<string,unknown>)[e.props.name]??{}
 return React.cloneElement(e,{...(override as object),...(e.props.children===undefined?{}:{children:React.Children.map(e.props.children,apply)})})
}
export default function TwoCapComparison({routingDisabled=true}:{routingDisabled?:boolean}={}){return apply(Board({routingDisabled}))}
