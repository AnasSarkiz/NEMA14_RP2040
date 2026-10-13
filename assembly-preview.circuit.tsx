import React from "react"
import { assembly } from "tscircuit"
import Controller from "./src/board"
// Visual space/harness concept only. The drawing proves front mount holes;
// it does not prove rear threads. No rear holes/screws are invented in this model.
// Factory leads are bare; the shown JST-SH termination is a proposed harness.
const model="nema17_bodywidth35.2mm_bodylength28.2mm_holespacing26mm_holediameter3mm_holedepth4mm_shaftlength24mm_shaftdiameter5mm_dshaft_flatdepth0.5mm_flatlength15mm_jstsh4_wireangle270deg"
export default function AssemblyConcept() {
 return <assembly.device name="NEMA14_HARNESS_CONCEPT_REAR_ADAPTER_UNVERIFIED">
  <Controller routingDisabled assemblyPreview />
  <assembly.motor name="MOTOR_REFERENCE_CONCEPT" displayName="14HM11-0404S concept — rear adapter unverified" model={model} shaftFacingDirection="z-" />
  <assembly.cable name="PROPOSED_JST_SH_HARNESS" from="MOTOR_REFERENCE_CONCEPT.wireside" to=".J_MOTOR" />
 </assembly.device>
}
