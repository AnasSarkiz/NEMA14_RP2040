/** Preserve the eight verified paths; author the existing same-net driver link. */
import React from 'react'
import Integrated from '../integrated/candidate'
export default function ReachabilityCandidate({routingDisabled=false}:{routingDisabled?:boolean}={}) {
 const root:any=Integrated({routingDisabled})
 return React.cloneElement(root,{},[root.props.children,<trace key="DRIVER_MODE_RESET" name="DRIVER_MODE_RESET" from=".U_DRV > .MS3" to=".U_DRV > .RESET_N" thickness={.16} pcbStraightLine />])
}
