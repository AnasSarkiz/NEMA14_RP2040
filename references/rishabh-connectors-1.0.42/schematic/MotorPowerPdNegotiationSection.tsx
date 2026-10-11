import { revisionPlacement } from "../mechanical/revision-placement";
import { CH224K } from "../imports/CH224K";
import { MotorUsbC } from "../imports/usb-c-20v";
import {
  groundTrace,
  logicTrace,
  powerTrace,
  schematicSections,
  schematicSheets,
} from "./config";

export const MotorPowerPdControllers = () => (
  <>
    <MotorUsbC
      name="J_MOTOR_USB"
      // Keep shell labels above/below the built-in USB graphic.
      schPinArrangement={{topSide:{pins:[6],direction:"left-to-right"},rightSide:{pins:[15,8,14,10,12,11,9,13,7,16],direction:"top-to-bottom"},bottomSide:{pins:[5],direction:"left-to-right"},leftSide:{pins:[1,2,3,4],direction:"top-to-bottom"}}}
      schWidth={3} schHeight={3.95}
      schPinStyle={{...Object.fromEntries([8,14,10,12,11,9,13,7,16].map(pin=>[`pin${pin}`,{marginTop:0.2}])),pin2:{marginTop:0.1},pin3:{marginTop:2.6},pin4:{marginTop:0.1}}}
      noConnect={["B8", "A8"]}
      pcbX={12.625}
      pcbY={24.95}
      pcbRotation={180}
      schSheetName={schematicSheets.motorPower}
      schSectionName={schematicSections.pdNegotiation}
    />
    <CH224K
      name="U_PD" schWidth={1.8} schHeight={1.77}
      schMarginRight={1}
      schPinArrangement={{
        leftSide: {
          pins: [4, 5, 6, 7],
          direction: "top-to-bottom",
        },
        rightSide: {
          pins: [10, 9, 2, 3, 8],
          direction: "top-to-bottom",
        },
        topSide: {
          pins: [1],
          direction: "left-to-right",
        },
        bottomSide: {
          pins: [11],
          direction: "left-to-right",
        },
      }}
      schPinStyle={{
        pin6: { marginTop: 0.4 },
        pin8: { marginTop: 0.4 },
      }}
      schSheetName={schematicSheets.motorPower}
      schSectionName={schematicSections.pdNegotiation}
     {...revisionPlacement("U_PD", {x:-5.625,y:-8.25})} />
  </>
);

export const MotorPowerPdPassives = () => (
  <>
    <capacitor
      name="C_PD_VDD"
      capacitance="1uF"
      footprint="0603"
      supplierPartNumbers={{ jlcpcb: ["C15849"] }}
      maxDecouplingTraceLength={10}
      schOrientation="vertical"
      schSheetName={schematicSheets.motorPower}
      schSectionName={schematicSections.pdNegotiation} {...revisionPlacement("C_PD_VDD", {x:-5.625,y:-8.25})}
    />
    <resistor
      name="R_PD_VDD" schRotation={90.0}
      resistance="1k"
      footprint="1206"
      // 327 mW worst case at 21 V / 3 V VDD / 990 ohm: use a 750 mW part.
      supplierPartNumbers={{ jlcpcb: ["C844867"] }}
      manufacturerPartNumber="CRCW12061K00FKEAHP"
      schMarginX={0.25}
      schMarginY={0.2}
      schSheetName={schematicSheets.motorPower}
      schSectionName={schematicSections.pdNegotiation} {...revisionPlacement("R_PD_VDD", {x:-5.625,y:-8.25})}
    />
    <resistor
      name="R_PD_VBUS" schRotation={180.0}
      resistance="10k"
      footprint="0402"
      supplierPartNumbers={{ jlcpcb: ["C25744"] }}
      schMarginX={0.25}
      schMarginY={0.2}
      schSheetName={schematicSheets.motorPower}
      schSectionName={schematicSections.pdNegotiation} {...revisionPlacement("R_PD_VBUS", {x:-5.625,y:-8.25})}
    />

  </>
);

export const MotorPowerPdInputTraces = () => (
  <>
    <trace
      name="MOTOR_VBUS_JOIN"
      from=".J_MOTOR_USB > .A4B9"
      to=".J_MOTOR_USB > .B4A9"
      {...powerTrace}
    />
    <trace
      name="MOTOR_VBUS_VM"
      from=".D_MOTOR_BLOCK > .cathode"
      to=".DRIVER > .VM"
      schDisplayLabel="VMOTOR_PROTECTED"
      {...powerTrace}
    />
  </>
);

export const MotorPowerPdProtocolTraces = () => (
  <>
    <trace
      name="PD_VDD_FEED"
      from=".J_MOTOR_USB > .A4B9"
      to=".R_PD_VDD > .pin1"
      {...logicTrace}
    />
    <trace
      name="PD_VBUS_SENSE_FEED"
      from=".J_MOTOR_USB > .A4B9"
      to=".R_PD_VBUS > .pin1"
      {...logicTrace}
    />
    <trace
      name="PD_VDD_INPUT"
      from=".R_PD_VDD > .pin2"
      to=".U_PD > .VDD"
      schDisplayLabel="PD_VDD"
      {...logicTrace}
    />
    <trace
      name="PD_VBUS_INPUT"
      from=".R_PD_VBUS > .pin2"
      to=".U_PD > .VBUS"
      schDisplayLabel="PD_VBUS"
      {...logicTrace}
    />
    <trace
      name="PD_VDD_DECOUPLE"
      from=".U_PD > .VDD"
      to=".C_PD_VDD > .pin1"
      {...logicTrace}
    />
    <trace
      name="PD_CC1"
      from=".J_MOTOR_USB > .A5"
      to=".U_PD > .CC1"
      schDisplayLabel="CC1"
      {...logicTrace}
    />
    <trace
      name="PD_CC2"
      from=".J_MOTOR_USB > .B5"
      to=".U_PD > .CC2"
      schDisplayLabel="CC2"
      {...logicTrace}
    />
    <trace
      name="PD_DP_A"
      from=".J_MOTOR_USB > .A6"
      to=".U_PD > .DP"
      schDisplayLabel="USB_D+"
      {...logicTrace}
    />
    <trace
      name="PD_DP_JOIN"
      from=".J_MOTOR_USB > .B6"
      to=".J_MOTOR_USB > .A6"
      {...logicTrace}
    />
    <trace
      name="PD_DM_A"
      from=".J_MOTOR_USB > .A7"
      to=".U_PD > .DM"
      schDisplayLabel="USB_D-"
      {...logicTrace}
    />
    <trace
      name="PD_DM_JOIN"
      from=".J_MOTOR_USB > .B7"
      to=".J_MOTOR_USB > .A7"
      {...logicTrace}
    />
  </>
);

export const MotorPowerPdPrimaryGroundTrace = () => (
  <>
    <trace
      name="MOTOR_USB_GND_A"
      from=".J_MOTOR_USB > .A1B12"
      to=".DRIVER > .EP"
      {...groundTrace}
    />
  </>
);

export const MotorPowerPdConnectorGroundTraces = () => (
  <>
    <trace
      name="MOTOR_USB_GND_JOIN"
      from=".J_MOTOR_USB > .B1A12"
      to=".J_MOTOR_USB > .A1B12"
      {...groundTrace}
    />
    <trace
      name="MOTOR_USB_SHIELD_1"
      from=".J_MOTOR_USB > .EH1"
      to=".J_MOTOR_USB > .A1B12"
      {...groundTrace}
    />
    <trace
      name="MOTOR_USB_SHIELD_2"
      from=".J_MOTOR_USB > .EH2"
      to=".J_MOTOR_USB > .A1B12"
      {...groundTrace}
    />
    <trace
      name="MOTOR_USB_SHIELD_3"
      from=".J_MOTOR_USB > .EH3"
      to=".J_MOTOR_USB > .A1B12"
      {...groundTrace}
    />
    <trace
      name="MOTOR_USB_SHIELD_4"
      from=".J_MOTOR_USB > .EH4"
      to=".J_MOTOR_USB > .A1B12"
      {...groundTrace}
    />
    <trace
      name="PD_GND"
      from=".U_PD > .GND"
      to=".DRIVER > .EP"
      {...groundTrace}
    />
  </>
);

export const MotorPowerPdSupportGroundTraces = () => (
  <>
    <trace
      name="PD_VDD_CAP_GND"
      from=".C_PD_VDD > .pin2"
      to="net.GND"
      {...logicTrace}
    />
  </>
);
