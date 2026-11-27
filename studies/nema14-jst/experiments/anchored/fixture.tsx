/** Separate native anchored-copper experiment. Never changes accepted placement. */
import React from 'react'
import {Via,Port} from '@tscircuit/core'
import BareCandidate from '../compact/candidate'
import partNames from '../compact/source-names.json'
import guarded from '../compact/scope.json'
import spec from './generated.json'
import options from './design-options.json'
const coupon=['U_DRV','R_SA','R_SB','R_SHUNT_A','R_SHUNT_B','U_IA','U_IB','C_IA','C_IB','C_VM','C_BULK','C_CP','C_VCP','C_VREG','C_DRV_LOGIC','J_MOTOR','J_PD','J_DATA','U_ENCODER','C_ENCODER','C_ENCODER_BULK']
function bind(v:Via|null){if(!v)return;for(const layer of ['inner1','inner2'] as const){if(v.children.some((p:any)=>p.props?.name===layer))continue;const p=new Port({name:layer,layer});p.registerMatch(v);v.add(p)}}
export type Scope='coupon'|'guarded'|'board'
export default function Fixture({scope='coupon',routingDisabled=true,smallStar=false,copper=true,forceSingular=false,allPlural=false,anchorShift=0,adapter,boardRef}:{scope?:Scope,routingDisabled?:boolean,smallStar?:boolean,copper?:boolean,forceSingular?:boolean,allPlural?:boolean,anchorShift?:number,adapter?:any,boardRef?:any}={}){
 const allowed=scope==='coupon'?coupon:scope==='guarded'?guarded:partNames
 const fragments:any[]=[]
 function visit(node:any):any{if(!React.isValidElement(node))return node;const e=node as React.ReactElement<any>,name=e.props.name;const pose=(options.poses as Record<string,number[]>)[name];if(partNames.includes(name)&&!allowed.includes(name))return null;const r=(spec.paths as any)[name];if(r&&copper)return null;return React.cloneElement(e,{...(pose?{pcbX:pose[0],pcbY:pose[1],pcbRotation:pose[2]}:{}),...(name==='R_SHUNT_A'&&anchorShift?{pcbX:e.props.pcbX+anchorShift}:{}),...(e.props.children!==undefined?{children:React.Children.map(e.props.children,visit)}:{})})}
 const root:any=visit(BareCandidate({scope:false,routingDisabled,copper:false}));const extra=copper?[...(spec as any).fragments.map((r:any)=><trace key={r.name} name={r.name} from={r.from} to={r.to} thickness={r.width_mm} pcbPathRelativeTo={r.anchor} {...((!allPlural&&r.representation==='singular')||forceSingular?{pcbPath:r.path}:{pcbPaths:r.paths})}/>),...spec.vias.map((v:any)=><via {...({key:v.name,ref:bind} as any)} name={v.name} pcbX={v.x} pcbY={v.y} fromLayer="top" toLayer="bottom" outerDiameter={v.name.startsWith('V_STAR_')||(v.name==='V_GB'||v.name==='V_KBN_S')?.45:.55} holeDiameter={smallStar&&(v.name.startsWith('V_STAR_')||(v.name==='V_GB'||v.name==='V_KBN_S'))?.2:.3} connectsTo={'net.'+v.net}/>)]:[]
 return React.cloneElement(root,{...(adapter?{autorouter:{algorithmFn:adapter}}:{}),...(boardRef?{ref:boardRef}:{}),...(smallStar?{minViaHoleDiameter:.2}:{}),pcbStyle:{viaPadDiameter:.45,viaHoleDiameter:smallStar?.2:.3}},[root.props.children,...extra])
}
