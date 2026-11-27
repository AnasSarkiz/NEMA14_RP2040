/** Separate VREG ground-loop candidate; no via/process/placement or prior-copper change. */
import React from 'react'
import Base from '../vreg-star/candidate'
import path from './path.json'
export default function Candidate(){const root:any=Base();return React.cloneElement(root,{},[root.props.children,<trace key={path.name} name={path.name} from={path.from} to={path.to} thickness={path.width_mm} pcbPathRelativeTo={path.anchor} pcbPaths={[path.local_points]}/>])}
