/** Legal through-via between rounded same-net pad ends; all existing paths fixed. */
import React from 'react'
import Returns from './returns'
import ThroughVia from './through-via'
export default function Escape({routingDisabled=false}:{routingDisabled?:boolean}={}){
 const root:any=Returns({routingDisabled})
 return React.cloneElement(root,{},[root.props.children,<ThroughVia name="V_MODE" x={8.449303} y={1.7006} net="V3V3"/>,<trace name="MODE_ESCAPE" from=".U_DRV > .MS3" to=".V_MODE > .top" thickness={.16} pcbPaths={[[ '.U_DRV > .MS3','.V_MODE > .top' ]]}/>])
}
