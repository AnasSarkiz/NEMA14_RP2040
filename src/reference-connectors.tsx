import React, { Children, cloneElement, type ReactElement } from "react"
import { USB4145_03_0070_C } from "../imports/supplier/USB4145_03_0070_C/USB4145_03_0070_C"
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

const usb = USB4145_03_0070_C({ name: "USB" })
const usbLabels = {...usb.props.pinLabels, pin6:["DM1","DN1","A7"], pin10:["DM2","DN2","B7"], pin17:["EH1","SHELL1"],pin18:["EH2","SHELL2"],pin19:["EH3","SHELL3"],pin20:["EH4","SHELL4"]}
export const StandardUsbConnector = (props:any) => (
 <connector {...USB4145_03_0070_C(props as any).props} standard="usb_c" pinLabels={usbLabels} footprint={footprint(usb,"pin17",17)} {...props} />
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
