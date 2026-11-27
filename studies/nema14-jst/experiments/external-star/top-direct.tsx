/** Distinct top-side current-path control; does not qualify the narrow intermediate ground lands. */
import React from 'react'
import Base from './candidate'
import paths from './direct-paths.json'
export default function Candidate(){const replacement=new Map((paths as any[]).map(p=>[p.name,p]));function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,p=replacement.get(e.props.name);if(e.props.name?.startsWith('RETURN_')&&e.props.name.endsWith('_INNER'))return null;if(p)return <trace key={p.name} name={p.name} from={p.from} to={p.to} thickness={p.width_mm} pcbPathRelativeTo={p.anchor} pcbPaths={[p.local_points]}/>;return React.cloneElement(e,e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})}return visit(Base())}
