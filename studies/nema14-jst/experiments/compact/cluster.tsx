/** Diagnostic subset only. This entry does not represent a completed controller. */
import React from 'react'
import Candidate from './candidate'
export default function Cluster({routingDisabled=true}:{routingDisabled?:boolean}={}) { return <Candidate routingDisabled={routingDisabled} scope/> }
