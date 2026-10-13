import React, { Children, cloneElement, type ReactElement } from "react"
import { TYPE_C_31_M_12 } from "../imports/supplier/TYPE_C_31_M_12/TYPE_C_31_M_12"
import { BM04B_SRSS_TB_LF__SN_ } from "../imports/supplier/BM04B_SRSS_TB_LF__SN_/BM04B_SRSS_TB_LF__SN_"

// Keep the exact supplier land patterns and CAD. Split common mechanical pads
// into source terminals so every real shell tab/hold-down is checked and routed.
function footprint(element: any, commonPin: string, firstPin: number) {
  let terminal = firstPin
  const fp = element.props.footprint as ReactElement<any>
  return cloneElement(fp, { insertionDirection: "from_above" }, Children.map(fp.props.children, child => {
    const pad = child as ReactElement<any>
    if (!pad.props.portHints?.includes(commonPin)) return pad
    return cloneElement(pad, { portHints: [`pin${terminal++}`] })
  }))
}

const usb = TYPE_C_31_M_12({ name: "USB" })
const usbLabels = {...usb.props.pinLabels, pin7:["DM2","DN2","B7"], pin9:["DM1","DN1","A7"], pin1:["EH2","SHELL2"],pin2:["EH1","SHELL1"],pin3:["EH4","SHELL4"],pin4:["EH3","SHELL3"]}
export const StandardUsbConnector = (props:any) => (
 <connector {...TYPE_C_31_M_12(props as any).props} standard="usb_c" pinLabels={usbLabels} {...props} />
)

const motor = BM04B_SRSS_TB_LF__SN_({ name: "MOTOR" })
const motorLabels = {
  pin1: ["A_PLUS"], pin2: ["A_MINUS"], pin3: ["B_PLUS"], pin4: ["B_MINUS"],
  pin5: ["MOUNT1"], pin6: ["MOUNT2"],
}
export const SmtMotorConnector = (props: any) => (
  <connector {...motor.props} standard="jst_sh" pinCount={4} pinLabels={motorLabels}
    footprint={footprint(motor, "pin5", 5)} {...props} />
)
