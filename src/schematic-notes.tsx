import React from "react"
import notes from "./schematic-notes.json"

export const SchematicNotes = () => <>
  <schematictext text="NEMA14_RP2040 - USB-C NEMA14 MOTOR CONTROLLER" schX={-15} schY={10.35} fontSize={0.3} anchor="top_left" />
  <schematictext text="COMPONENT PURPOSE" schX={8} schY={9.3} fontSize={0.28} anchor="top_left" />
  {notes.map(([title, purpose], i) => <React.Fragment key={title}>
    <schematictext text={title} schX={8} schY={8.6-i*2.35} fontSize={0.23} anchor="top_left" />
    <schematictext text={purpose} schX={8} schY={8.2-i*2.35} fontSize={0.19} anchor="top_left" />
  </React.Fragment>)}
  <schematictext text="PD PORT: motor power, 15 V requested. DATA PORT: USB computer control.\nMotor: 14HM11-0404S, bipolar, 0.4 A/phase. Prototype: firmware/bench/rear-fit validation pending."
    schX={-15} schY={-9.45} fontSize={0.19} anchor="top_left" />
</>
