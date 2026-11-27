/** Actual native return copper on the unchanged placement. Length gates still apply. */
import React from 'react'
import Candidate from './candidate'
import ThroughVia from './through-via'
import paths from './return-paths.json'
export default function Returns({routingDisabled=false}:{routingDisabled?:boolean}={}){
 const root:any=Candidate({routingDisabled})
 const extra:React.ReactNode[]=[<ThroughVia key="star" name="V_STAR" x={paths.star[0]} y={paths.star[1]}/>]
 for(const phase of ['A','B'] as const){const v=paths.source_vias[phase],selector='.V_RETURN_'+phase
  extra.push(<ThroughVia key={phase} name={'V_RETURN_'+phase} x={v[0]} y={v[1]}/>)
  extra.push(<trace key={phase+'top'} name={'RETURN_'+phase+'_TOP'} from={'.R_S'+phase+' > .pin2'} to={selector+' > .top'} thickness={.6} pcbPaths={[[ '.R_S'+phase+' > .pin2',selector+' > .top' ]]}/>)
  // Coordinate anchors are relative to the source via; selectors own real ports.
  extra.push(<trace key={phase+'inner'} name={'RETURN_'+phase+'_INNER1'} from={selector+' > .inner1'} to=".V_STAR > .inner1" thickness={.6} pcbPaths={[[selector+' > .inner1',...paths.inner1[phase].slice(1,-1).map(p=>({x:p[0]-v[0],y:p[1]-v[1]})),'.V_STAR > .inner1']]}/>)
 }
 extra.push(<trace key="ep" name="STAR_TO_EP" from=".V_STAR > .top" to=".U_DRV > .EP" thickness={.6} pcbPaths={[[ '.V_STAR > .top','.U_DRV > .EP' ]]}/>)
 return React.cloneElement(root,{},[root.props.children,...extra])
}
