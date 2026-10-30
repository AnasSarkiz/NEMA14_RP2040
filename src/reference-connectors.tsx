import React, { Children, cloneElement, type ReactElement } from "react"
import { USB4145_03_0070_C } from "../imports/supplier/USB4145_03_0070_C/USB4145_03_0070_C"
import { BM04B_SRSS_TB_LF__SN_ } from "../imports/supplier/BM04B_SRSS_TB_LF__SN_/BM04B_SRSS_TB_LF__SN_"
import { A_1770979 } from "../imports/supplier/A_1770979/A_1770979"

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

// Preserve both physical PCB contacts for each Phoenix terminal pole.
const spring = A_1770979({name:"MOTOR"})
function springFootprint(){
  const fp=spring.props.footprint as ReactElement<any>
  const counts=[0,0,0,0]
  const result=cloneElement(fp,{},Children.map(fp.props.children,child=>{
    const pad=child as ReactElement<any>
    if(!pad.props.portHints)return pad
    const match=pad.props.portHints[0]?.match(/^pin([1-4])$/)
    if(!match)throw Error("Unexpected Phoenix terminal contact")
    const pole=Number(match[1])-1,contact=counts[pole]++
    return cloneElement(pad,{portHints:[`pin${pole*2+contact+1}`]})
  }))
  if(counts.some(n=>n!==2))throw Error("Phoenix terminal must have two contacts per pole")
  return result
}
export const SpringMotorConnector = (props:any)=>(
  <connector {...spring.props} pinCount={8} footprint={springFootprint()}
    pinLabels={{pin1:["A_PLUS"],pin2:["A_PLUS_2"],pin3:["A_MINUS"],pin4:["A_MINUS_2"],
      pin5:["B_PLUS"],pin6:["B_PLUS_2"],pin7:["B_MINUS"],pin8:["B_MINUS_2"]}} {...props} />
)
