import React from "react"
import { assembly, jscad } from "tscircuit"
import { renderToJscadPlan } from "jscad-fiber"
import Controller from "./src/board"
import qualifiedBoard from "./index.circuit.json"
import { getMotorHarness } from "./src/motor-harness"

// The supplier drawing verifies FRONT holes only. Rear attachment remains a
// proposed interface: no rear threads, rear shaft or magnet are invented.
const model = "nema17_bodywidth35.2mm_bodylength28.2mm_holespacing26mm_holediameter3mm_holedepth4mm_shaftlength24mm_shaftdiameter5mm_dshaft_flatdepth0.5mm_flatlength15mm_nowires_wireangle270deg"
const harness = getMotorHarness(qualifiedBoard)
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
    {harness.wirePlans.map((plan,i)=><assembly.part key={`lead_${i}`}
      name={`MOTOR_LEAD_PIN_${i+1}`} displayName={`${harness.wires[i].color} motor lead to JST pin ${i+1}`}
      cadModel={{jscad:plan,modelOriginPosition:{x:0,y:0,z:0}}} />)}
    {harness.splicePlans.map((plan,i)=><assembly.part key={`splice_${i}`}
      name={`MOTOR_SPLICE_PIN_${i+1}`} displayName={`Insulated pigtail splice, pin ${i+1}`}
      cadModel={{jscad:plan,modelOriginPosition:{x:0,y:0,z:0}}} />)}
    <assembly.part name="JST_SHR_04V_S_PLUG"
      displayName="SHR-04V-S seated in BM04B-SRSS-TB; exposed catalog outline"
      cadModel={{jscad:harness.housingPlan,
        positionOffset:{x:harness.body_origin.x,y:harness.body_origin.y,z:0},
        rotationOffset:{x:0,y:0,z:harness.body_rotation_z},modelOriginPosition:{x:0,y:0,z:0}}} />
  </assembly.device>
}
