import { Fragment } from "react";
import { LTST_C19HE1WT } from "../imports/LTST_C19HE1WT";
import { DTC114EU3HZGT106 } from "../imports/DTC114EU3HZGT106";
import { revisionPlacement as p } from "../mechanical/revision-placement";
const sch = {schSheetName:"status_led", schSectionName:"rgb"};

export const StatusLedSection = () => <>
  <schematicsheet name="status_led" displayName="RGB Status Indicator" sheetIndex={8}><schematicsection name="rgb" displayName="Status"/></schematicsheet>
  <LTST_C19HE1WT name="D_STATUS" {...p("D_STATUS")} {...sch}/>
  {/* Programming USB VBUS is fixed 5 V; never use the negotiated motor PD rail. */}
  <trace name="STATUS_5V" from=".MCU > .J_USB > .A4B9" to=".D_STATUS > ._POS" schDisplayLabel="USB_5V" thickness="0.2mm"/>
  {(["R","G","B"] as const).map((color,index) => {
    const q=`Q_STATUS_${color}`, r=`R_STATUS_${color}`, x=index*5-5;
    return <Fragment key={color}>
      <resistor name={r} resistance="1k" footprint="0402" supplierPartNumbers={{jlcpcb:["C11702"]}}
        {...p(r)} {...sch} schOrientation="vertical"/>
      <DTC114EU3HZGT106 name={q} {...p(q)} {...sch}/>
      <trace name={`STATUS_${color}_LED`} from={`.D_STATUS > .${color}_NEG`} to={`.${r} > .pin1`} thickness="0.15mm"/>
      <trace name={`STATUS_${color}_SINK`} from={`.${r} > .pin2`} to={`.${q} > .C`} thickness="0.15mm"/>
      <trace name={`STATUS_${color}_GND`} from={`.${q} > .E`} to="net.GND" thickness="0.15mm"/>
      <trace name={`STATUS_${color}_GPIO`} from={`.MCU > .U1 > .GPIO${[25,2,3][index]}`} to={`.${q} > .B`} schDisplayLabel={`LED_${color}`} thickness="0.15mm"/>
    </Fragment>;
  })}
</>;
