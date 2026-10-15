import React from "react"
import { assembly, jscad } from "tscircuit"
import { renderToJscadPlan } from "jscad-fiber"
import Controller from "./src/board"

// The supplier drawing verifies FRONT holes only. Rear attachment remains a
// proposed interface: no rear threads, rear shaft or magnet are invented.
const model = "nema17_bodywidth35.2mm_bodylength28.2mm_holespacing26mm_holediameter3mm_holedepth4mm_shaftlength24mm_shaftdiameter5mm_dshaft_flatdepth0.5mm_flatlength15mm_jstsh4_wireangle60deg"
export const mounts = [-13, 13].flatMap(x => [-13, 13].map(y => ({ x, y })))

function Screw() {
  // Approved nominal Ø4 x 3 mm head; M3 x 6 shaft. Threads are schematic.
  return <jscad.colorize color={[0.65, 0.67, 0.70]}>
    <jscad.subtract>
      <jscad.union>
        <jscad.cylinder radius={2} height={3} center={[0, 0, 2.3]} />
        <jscad.cylinder radius={1.5} height={6} center={[0, 0, -2.2]} />
      </jscad.union>
      <jscad.cuboid size={[4.2, 0.65, 0.8]} center={[0, 0, 3.6]} />
    </jscad.subtract>
  </jscad.colorize>
}
function Spacer() {
  return <jscad.colorize color={[0.78, 0.79, 0.80]}>
    <jscad.subtract>
      <jscad.cylinder radius={2.5} height={6} center={[0, 0, -3.8]} />
      <jscad.cylinder radius={1.6} height={6.2} center={[0, 0, -3.8]} />
    </jscad.subtract>
  </jscad.colorize>
}
export default function AssemblyConcept() {
  return <assembly.device name="NEMA14_ASSEMBLY_REAR_ATTACHMENT_UNVERIFIED">
    <Controller routingDisabled assemblyPreview />
    <assembly.motor name="MOTOR_REFERENCE_CONCEPT"
      displayName="14HM11-0404S dimensional concept; rear attachment unverified"
      model={model} shaftFacingDirection="z-" />
    {mounts.map(({ x, y }) => <React.Fragment key={`${x},${y}`}>
      <assembly.part name={`PROPOSED_M3_SCREW_${x}_${y}`}
        displayName="Proposed M3 x 6, Ø4 x 3 head; supplier approval pending"
        cadModel={{ jscad: renderToJscadPlan(<Screw />), positionOffset: { x, y, z: 0 } }} />
      <assembly.part name={`PROPOSED_SPACER_${x}_${y}`}
        displayName="Proposed 6 mm spacer; rear retention unverified"
        cadModel={{ jscad: renderToJscadPlan(<Spacer />), positionOffset: { x, y, z: 0 } }} />
    </React.Fragment>)}
    <assembly.cable name="PROPOSED_JST_SH_HARNESS"
      from="MOTOR_REFERENCE_CONCEPT.wireside" to=".J_MOTOR" />
  </assembly.device>
}
