import React from "react"
import { SupplierPart } from "./supplier-parts"
import placements from "./supplier-placement.json"
const n = (name:string) => `net.${name}`
const place = (name:string) => (placements as Record<string,{pcbX:number,pcbY:number,pcbRotation:number}>)[name]
/** Fitted top-side diagnostics. Firmware is required for temperature readout/alarm. */
export function Diagnostics() {
 return <>
  {['TEMP_SCL','TEMP_SDA','TEMP_ALERT_N','STATUS_N','LED_ANODE','BUZZER_PWM','BUZZER_GATE','BUZZER_SINK'].map(name => <React.Fragment key={name}><net name={name} nominalTraceWidth={name==='BUZZER_SINK'?0.30:0.16} /></React.Fragment>)}
  <SupplierPart name="D_STATUS" {...place('D_STATUS')} connections={{anode:n('LED_ANODE'),cathode:n('STATUS_N')}} />
  <SupplierPart name="R_LED" resistance="1k" tolerance="1%" {...place('R_LED')} connections={{pin1:n('V3V3'),pin2:n('LED_ANODE')}} />
  <SupplierPart name="U_TEMP" {...place('U_TEMP')} connections={{SCL:n('TEMP_SCL'),GND:n('GND'),ALERT:n('TEMP_ALERT_N'),ADD0:n('GND'),V_POS:n('V3V3'),SDA:n('TEMP_SDA')}} />
  <SupplierPart name="C_TEMP" capacitance="100nF" {...place('C_TEMP')} connections={{pin1:n('V3V3'),pin2:n('GND')}} />
  {['SCL','SDA'].map(signal=><SupplierPart key={signal} name={'R_TEMP_'+signal} resistance="5.1k" tolerance="1%" {...place('R_TEMP_'+signal)} connections={{pin1:n('V3V3'),pin2:n('TEMP_'+signal)}} />)}
  <SupplierPart name="R_TEMP_ALERT" resistance="10k" tolerance="1%" {...place('R_TEMP_ALERT')} connections={{pin1:n('V3V3'),pin2:n('TEMP_ALERT_N')}} />
  <SupplierPart name="BZ_ALARM" {...place('BZ_ALARM')} noConnect={['NC']} connections={{_POS:n('V3V3'),_NEG:n('BUZZER_SINK')}} />
  <SupplierPart name="Q_BUZZER" {...place('Q_BUZZER')} connections={{G:n('BUZZER_GATE'),S:n('GND'),D:n('BUZZER_SINK')}} />
  <SupplierPart name="D_BUZZER" {...place('D_BUZZER')} connections={{anode:n('BUZZER_SINK'),cathode:n('V3V3')}} />
  <SupplierPart name="R_BUZZER_GATE" resistance="100" tolerance="1%" {...place('R_BUZZER_GATE')} connections={{pin1:n('BUZZER_PWM'),pin2:n('BUZZER_GATE')}} />
  <SupplierPart name="R_BUZZER_PD" resistance="100k" tolerance="1%" {...place('R_BUZZER_PD')} connections={{pin1:n('BUZZER_GATE'),pin2:n('GND')}} />
  <SupplierPart name="C_BUZZER" capacitance="22uF" {...place('C_BUZZER')} connections={{pin1:n('V3V3'),pin2:n('GND')}} />
 </>
}
