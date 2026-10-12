import { revisionPlacement } from "../mechanical/revision-placement";
import { Fragment } from "react";
import { HYG_8503A } from "../imports/HYG_8503A";
import { AO3400A } from "../imports/AO3400A";
import { B5819W_SL } from "../imports/B5819W_SL";

const alarm = { schSheetName: "position_alarm", schSectionName: "alarm" } as const;
const signal = { thickness: "0.15mm" } as const;
const supply = { thickness: "0.3mm" } as const;

/** Audible overtemperature alarm. An optional DNP shaft encoder shares this sheet. */
export const FeedbackSection = () => <>
  <schematicsheet name="position_alarm" displayName="Optional Encoder & Audible Alarm" sheetIndex={6}>
    <schematicsection name="encoder" displayName="Optional Shaft Position (DNP)" />
    <schematicsection name="alarm" displayName="Temperature Alarm" />
    <schematicsection name="feedback_supply" displayName="3.3 V Bypass" />
  </schematicsheet>
  <HYG_8503A name="BZ1" layer="top" {...revisionPlacement("BZ1")} noConnect={["NC1","NC2"]} {...alarm}/>
  <AO3400A name="Q_BUZZER" layer="top" {...alarm} {...revisionPlacement("Q_BUZZER")}/>
  <B5819W_SL name="D_BUZZER" layer="top" schRotation={90} {...alarm} {...revisionPlacement("D_BUZZER")}/>
  <resistor name="R_BUZZER_GATE" resistance="100" footprint="0402" supplierPartNumbers={{jlcpcb:["C25076"]}}
    layer="top" {...alarm} {...revisionPlacement("R_BUZZER_GATE")}/>
  <resistor name="R_BUZZER_PD" resistance="100k" footprint="0402" supplierPartNumbers={{jlcpcb:["C25741"]}}
    layer="top" schOrientation="vertical" {...alarm} {...revisionPlacement("R_BUZZER_PD")}/>
  <capacitor name="C_BUZZER" capacitance="10uF" footprint="0603" supplierPartNumbers={{jlcpcb:["C19702"]}}
    layer="top" maxDecouplingTraceLength={6} schOrientation="vertical" {...alarm} schSectionName="feedback_supply" {...revisionPlacement("C_BUZZER")}/>
  <trace name="BUZZER_PWM" from=".MCU > .U1 > .GPIO16" to=".R_BUZZER_GATE > .pin1" schDisplayLabel="BUZZER_PWM" {...signal}/>
  <trace name="BUZZER_GATE" from=".R_BUZZER_GATE > .pin2" to=".Q_BUZZER > .G" {...signal}/>
  <trace name="BUZZER_OFF" from=".Q_BUZZER > .G" to=".R_BUZZER_PD > .pin1" {...signal}/>
  <trace name="BUZZER_PD_GND" from=".R_BUZZER_PD > .pin2" to="net.GND" {...signal}/>
  <trace name="BUZZER_SOURCE" from=".Q_BUZZER > .S" to="net.GND" {...supply}/>
  <trace name="BUZZER_SINK" schDisplayLabel="BUZZER_SINK" from=".Q_BUZZER > .D" to=".BZ1 > ._NEG" {...supply}/>
  <trace name="BUZZER_VCC" from=".BZ1 > ._POS" to=".MCU > .L_AVDD > .pin1" schDisplayLabel="V3V3" {...supply}/>
  <trace name="BUZZER_FLYBACK_A" schDisplayLabel="BUZZER_SINK" from=".D_BUZZER > .anode" to=".Q_BUZZER > .D" {...supply}/>
  <trace name="BUZZER_FLYBACK_K" from=".D_BUZZER > .cathode" to=".BZ1 > ._POS" {...supply}/>
  <trace name="BUZZER_DECOUPLE" from=".C_BUZZER > .pin1" to=".BZ1 > ._POS" schDisplayLabel="V3V3" {...supply}/>
  <trace name="BUZZER_DECOUPLE_GND" from=".C_BUZZER > .pin2" to="net.GND" {...supply}/>
</>;
