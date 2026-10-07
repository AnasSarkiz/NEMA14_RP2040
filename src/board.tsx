import React from "react"
import { pinProps } from "./pin-attributes"
import { jlcProps } from "./jlcpcb"
import { SchematicNotes } from "./schematic-notes"
import { A4988Footprint, CH224Footprint, EsdFootprint, BulkFootprint } from "./footprints"
import { RP2040Footprint, BuckFootprint, FlashFootprint, CrystalFootprint } from "./rp2040-footprints"
import { USB } from "./USB"

// 26 mm square mounting is a parameter, not a verified rear-motor dimension.
export const mechanical = { width: 35, height: 35, holePitch: 26, holeDiameter: 3.2 }
const n = (name: string) => `net.${name}`
const mcuPins = {"pin1": "IOVDD1", "pin2": "GPIO0", "pin3": "GPIO1", "pin4": "GPIO2", "pin5": "GPIO3", "pin6": "GPIO4", "pin7": "GPIO5", "pin8": "GPIO6", "pin9": "GPIO7", "pin10": "IOVDD10", "pin11": "GPIO8", "pin12": "GPIO9", "pin13": "GPIO10", "pin14": "GPIO11", "pin15": "GPIO12", "pin16": "GPIO13", "pin17": "GPIO14", "pin18": "GPIO15", "pin19": "TESTEN", "pin20": "XIN", "pin21": "XOUT", "pin22": "IOVDD22", "pin23": "DVDD23", "pin24": "SWCLK", "pin25": "SWDIO", "pin26": "RUN", "pin27": "GPIO16", "pin28": "GPIO17", "pin29": "GPIO18", "pin30": "GPIO19", "pin31": "GPIO20", "pin32": "GPIO21", "pin33": "IOVDD33", "pin34": "GPIO22", "pin35": "GPIO23", "pin36": "GPIO24", "pin37": "GPIO25", "pin38": "GPIO26", "pin39": "GPIO27", "pin40": "GPIO28", "pin41": "GPIO29", "pin42": "IOVDD42", "pin43": "ADC_AVDD", "pin44": "VREG_IN", "pin45": "VREG_OUT", "pin46": "USB_DM", "pin47": "USB_DP", "pin48": "USB_VDD", "pin49": "IOVDD49", "pin50": "DVDD50", "pin51": "QSPI_SD3", "pin52": "QSPI_SCLK", "pin53": "QSPI_SD0", "pin54": "QSPI_SD2", "pin55": "QSPI_SD1", "pin56": "QSPI_SS", "pin57": "GND"} as const
const driverPins = {pin1:"OUT2B",pin2:"ENABLE_N",pin3:"GND",pin4:"CP1",pin5:"CP2",pin6:"VCP",pin7:"NC7",pin8:"VREG",pin9:"MS1",pin10:"MS2",pin11:"MS3",pin12:"RESET_N",pin13:"ROSC",pin14:"SLEEP",pin15:"VDD",pin16:"STEP",pin17:"REF",pin18:"NC18",pin19:"DIR",pin20:"NC20",pin21:"OUT1B",pin22:"VBB1",pin23:"SENSE1",pin24:"OUT1A",pin25:"NC25",pin26:"OUT2A",pin27:"SENSE2",pin28:"VBB2",pin29:"EP"} as const
const pdPins = {pin1:"VDD",pin2:"CFG2",pin3:"CFG3",pin4:"DP",pin5:"DM",pin6:"CC2",pin7:"CC1",pin8:"VBUS",pin9:"CFG1",pin10:"PG",pin11:"GND"} as const
const usbPins = {pin1:"GND1",pin2:"GND2",pin3:"VBUS1",pin4:"VBUS2",pin5:"CC1",pin6:"CC2",pin7:"DP1",pin8:"DP2",pin9:"DM1",pin10:"DM2",pin11:"SBU1",pin12:"SBU2",pin13:"SHIELD"} as const
const baseUsb = {GND1:n("GND"),GND2:n("GND"),SHIELD:n("GND")}
const resistor = (name:string,value:string,x:number,y:number,a:string,b:string,footprint="0603",rotation=0) => <resistor key={name} name={name} {...jlcProps(name)} resistance={value} tolerance="1%" footprint={footprint} pcbX={x} pcbY={y} pcbRotation={rotation} connections={{pin1:n(a),pin2:n(b)}} />
const cap = (name:string,value:string,x:number,y:number,a:string,b="GND",footprint="0603",rotation=0) => <capacitor key={name} name={name} {...jlcProps(name)} capacitance={value} maxVoltageRating={['PD_VBUS','LOGIC_IN','BUCK_BST','CP1'].includes(a)||b==='PD_VBUS'?35:10} footprint={footprint} pcbX={x} pcbY={y} pcbRotation={rotation} connections={{pin1:n(a),pin2:n(b)}} />

export default function Nema14Controller({ routingDisabled = false }: { routingDisabled?: boolean } = {}) {
 return <board width={35} height={35} layers={4} thickness={1.6}
  routingDisabled={routingDisabled} minTraceWidth={0.16} minTraceToPadEdgeClearance={0.15} minPadEdgeToPadEdgeClearance={0.15}
  minViaHoleDiameter={0.2} minViaPadDiameter={0.4} minBoardEdgeClearance={0.25}
  autorouter={{local:true, traceClearance:0.15}} autorouterEffortLevel="2x" schAutoLayoutEnabled>
  <schematicsheet name="NEMA14_RP2040" sheetSize="A4">
  {['GND','PD_VBUS','V3V3','LOGIC_IN','DATA_VBUS','PD_VDD','PD_CC1','PD_CC2','DATA_CC1','DATA_CC2','USB_DP','USB_DM','STEP','DIR','ENABLE_N','SLEEP','PD_GOOD','DATA_PRESENT','VM_SENSE','VREF','CP1','CP2','VCP','VREG','SENSE1','SENSE2','A_PLUS','A_MINUS','B_PLUS','B_MINUS','V1V1','QSPI_SS','QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','MCU_DM','MCU_DP','XIN','XOUT','XTAL_OUT','RUN','SWCLK','SWDIO','BUCK_SW','BUCK_BST','BOOT_PAD'].map(name=><React.Fragment key={name}><net name={name} isGroundNet={name==='GND'} isPowerNet={['PD_VBUS','V3V3','LOGIC_IN','DATA_VBUS','PD_VDD','V1V1'].includes(name)} nominalTraceWidth={['PD_VBUS','A_PLUS','A_MINUS','B_PLUS','B_MINUS','SENSE1','SENSE2'].includes(name)?0.45:0.16} /></React.Fragment>)}
  {[-13,13].flatMap(x=>[-13,13].map(y=><React.Fragment key={`${x},${y}`}><hole name={`M${x}_${y}`} pcbX={x} pcbY={y} diameter={3.2} /><keepout pcbX={x} pcbY={y} shape="rect" width={5.4} height={5.4} layers={['top','bottom']} /><silkscreencircle pcbX={x} pcbY={y} radius={2.7} strokeWidth={0.1} /></React.Fragment>))}
  <USB name="J_PD" {...pinProps("J_PD")}  manufacturerPartNumber="TYPE-C-31-M-12" {...jlcProps("J_PD")} pinLabels={usbPins} pcbX={-13.85} pcbY={4.5} pcbRotation={270} noConnect={['DP1','DP2','DM1','DM2','SBU1','SBU2']} connections={{...baseUsb,VBUS1:n('PD_VBUS'),VBUS2:n('PD_VBUS'),CC1:n('PD_CC1'),CC2:n('PD_CC2')}} />
  <USB name="J_DATA" {...pinProps("J_DATA")}  manufacturerPartNumber="TYPE-C-31-M-12" {...jlcProps("J_DATA")} pinLabels={usbPins} pcbX={13.85} pcbY={4.5} pcbRotation={90} noConnect={['SBU1','SBU2']} connections={{...baseUsb,VBUS1:n('DATA_VBUS'),VBUS2:n('DATA_VBUS'),CC1:n('DATA_CC1'),CC2:n('DATA_CC2'),DP1:n('USB_DP'),DP2:n('USB_DP'),DM1:n('USB_DM'),DM2:n('USB_DM')}} />
  <chip name="U_PD" {...pinProps("U_PD")}  manufacturerPartNumber="CH224K" pinLabels={pdPins} footprint={<CH224Footprint />} pcbX={-3.4} pcbY={8.2} noConnect={['DP','DM']} connections={{VDD:n('PD_VDD'),CFG2:n('PD_VDD'),CFG3:n('PD_VDD'),CFG1:n('GND'),VBUS:n('PD_VBUS'),CC1:n('PD_CC1'),CC2:n('PD_CC2'),PG:n('PD_GOOD'),GND:n('GND')}} />
  {resistor('R_PD','1k',-8.5,11.7,'PD_VBUS','PD_VDD')}
  {cap('C_PD','1uF',-5.5,11.7,'PD_VDD')}
  {resistor('R_PG','10k',-.5,11.8,'V3V3','PD_GOOD')}
  <chip name="U_MCU" {...pinProps("U_MCU")}  manufacturerPartNumber="RP2040" {...jlcProps("U_MCU")} pinLabels={mcuPins} footprint={<RP2040Footprint />} pcbX={3.4} pcbY={0} noConnect={["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO11", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "GPIO19", "GPIO20", "GPIO21", "GPIO22", "GPIO23", "GPIO24", "GPIO25", "GPIO26", "GPIO27"]} connections={{IOVDD1:n("V3V3"),IOVDD10:n("V3V3"),IOVDD22:n("V3V3"),IOVDD33:n("V3V3"),IOVDD42:n("V3V3"),IOVDD49:n("V3V3"),DVDD23:n("V1V1"),DVDD50:n("V1V1"),VREG_OUT:n("V1V1"),ADC_AVDD:n("V3V3"),USB_VDD:n("V3V3"),VREG_IN:n("V3V3"),TESTEN:n("GND"),GND:n("GND"),GPIO6:n("STEP"),GPIO7:n("DIR"),GPIO8:n("ENABLE_N"),GPIO9:n("SLEEP"),GPIO10:n("PD_GOOD"),GPIO28:n("VM_SENSE"),GPIO29:n("DATA_PRESENT"),USB_DM:n("MCU_DM"),USB_DP:n("MCU_DP"),RUN:n("RUN"),SWCLK:n("SWCLK"),SWDIO:n("SWDIO"),XIN:n("XIN"),XOUT:n("XOUT"),QSPI_SS:n("QSPI_SS"),QSPI_SCLK:n("QSPI_SCLK"),QSPI_SD0:n("QSPI_SD0"),QSPI_SD1:n("QSPI_SD1"),QSPI_SD2:n("QSPI_SD2"),QSPI_SD3:n("QSPI_SD3")}} />
  {cap('C_IO1','100nF',-1.7,2.6,'V3V3','GND','0402',90)}
  {cap('C_IO10','100nF',-1.7,-1.2,'V3V3','GND','0402',90)}
  {cap('C_IO22','100nF',4,-5.4,'V3V3','GND','0402',270)}
  {cap('C_IO33','100nF',8.05,-1.2,'V3V3','GND','0402',90)}
  {cap('C_IO42','100nF',8.05,2.6,'V3V3','GND','0402',90)}
  {cap('C_IO49','100nF',3.9,5.3,'V3V3','GND','0402',90)}
  {cap('C_DV23','100nF',5.2,-5.4,'V1V1','GND','0402',90)}
  {cap('C_DV50','100nF',2.9,5.3,'V1V1','GND','0402',90)}
  {cap('C_USB','100nF',4.3,7.4,'V3V3','GND','0402',90)}
  {cap('C_ADC','100nF',6.9,5.3,'V3V3','GND','0402',90)}
  {cap('C_VREG_IN','1uF',6.5,7.4,'V3V3','GND','0402',90)}
  {cap('C_VREG_OUT','1uF',5.4,7.4,'V1V1','GND','0402',90)}
  <chip name="U_FLASH" {...pinProps("U_FLASH")}  manufacturerPartNumber="GD25Q16EEIGR" {...jlcProps("U_FLASH")} pinLabels={{pin1:'CS',pin2:'IO1',pin3:'IO2',pin4:'GND',pin5:'IO0',pin6:'CLK',pin7:'IO3',pin8:'VCC',pin9:'EP'}} footprint={<FlashFootprint />} pcbX={2.2} pcbY={8.6} connections={{CS:n('QSPI_SS'),IO1:n('QSPI_SD1'),IO2:n('QSPI_SD2'),GND:n('GND'),IO0:n('QSPI_SD0'),CLK:n('QSPI_SCLK'),IO3:n('QSPI_SD3'),VCC:n('V3V3'),EP:n('GND')}} />
  {cap('C_FLASH','100nF',2,11.4,'V3V3','GND','0402')}
  {resistor('R_FLASH_CS','10k',2,12.6,'V3V3','QSPI_SS','0402',0)}
  {resistor('R_BOOT','1k',5.3,12.7,'QSPI_SS','BOOT_PAD','0402')}
  <chip name="J_BOOT" {...pinProps("J_BOOT")}  cadModel={null} pinLabels={{pin1:'BOOT',pin2:'GND'}} footprint={<footprint>{[-.75,.75].map((x,i)=><React.Fragment key={i}><smtpad portHints={[`pin${i+1}`]} pcbX={x} pcbY={0} width={1} height={1.5} shape="rect" /></React.Fragment>)}<courtyardrect width={2.8} height={2} /></footprint>} pcbX={8.2} pcbY={15.5} connections={{BOOT:n('BOOT_PAD'),GND:n('GND')}} />
  <chip name="Y_MCU" {...pinProps("Y_MCU")}  pcbRotation={0} manufacturerPartNumber="ABM8-272-T3" {...jlcProps("Y_MCU")} pinLabels={{pin1:'XIN',pin2:'GND2',pin3:'XTAL_OUT',pin4:'GND4'}} footprint={<CrystalFootprint />} pcbX={1.1} pcbY={-6.16} connections={{XIN:n('XIN'),XTAL_OUT:n('XTAL_OUT'),GND2:n('GND'),GND4:n('GND')}} />
  {resistor('R_XOUT','1k',4.3,-7,'XOUT','XTAL_OUT','0402')}
  {cap('C_XIN','15pF',-1.55,-6,'XIN','GND','0402',90)}
  {cap('C_XOUT','15pF',5.5,-8.5,'XTAL_OUT','GND','0402',90)}
  {resistor('R_RUN','10k',6.9,-5.5,'V3V3','RUN','0402',90)}
  {resistor('R_DM','27',5.9,5.3,'MCU_DM','USB_DM','0402',90)}
  {resistor('R_DP','27',4.9,5.3,'MCU_DP','USB_DP','0402',90)}
  {resistor('R_CC1','5.1k',8.6,12,'DATA_CC1','GND')}
  {resistor('R_CC2','5.1k',13,16.4,'DATA_CC2','GND','0402')}
  {resistor('R_USB_SENSE_H','100k',4.7,15.7,'DATA_VBUS','DATA_PRESENT')}
  {resistor('R_USB_SENSE_L','100k',14.7,-1.65,'DATA_PRESENT','GND')}
  {resistor('R_VM_H','100k',-.5,14,'PD_VBUS','VM_SENSE')}
  {resistor('R_VM_L','22k',3,14.1,'VM_SENSE','GND')}
  {cap('C_VM_SENSE','10nF',12,-3.8,'VM_SENSE','GND','0402')}
  <chip name="U_BUCK" {...pinProps("U_BUCK")}  pcbRotation={180} manufacturerPartNumber="AP63203WU-7" {...jlcProps("U_BUCK")} pinLabels={{pin1:'FB',pin2:'EN',pin3:'VIN',pin4:'GND',pin5:'SW',pin6:'BST'}} footprint={<BuckFootprint />} pcbX={-8} pcbY={-2.85} connections={{FB:n('V3V3'),EN:n('LOGIC_IN'),VIN:n('LOGIC_IN'),GND:n('GND'),SW:n('BUCK_SW'),BST:n('BUCK_BST')}} />
  <inductor name="L_BUCK" inductance="4.7uH" manufacturerPartNumber="SRN4018-4R7M" footprint={<footprint><smtpad portHints={['pin1']} pcbX={-1.6} pcbY={0} width={1.3} height={3.5} shape="rect" /><smtpad portHints={['pin2']} pcbX={1.6} pcbY={0} width={1.3} height={3.5} shape="rect" /><courtyardrect width={4.9} height={4.5} /></footprint>} pcbX={-8} pcbY={-7.25} connections={{pin1:n('BUCK_SW'),pin2:n('V3V3')}} />
  {cap('C_BOOTSTRAP','100nF',-5.2,-3.3,'BUCK_BST','BUCK_SW','0402')}
  {cap('C_BUCK_IN','10uF',-12,-2.3,'LOGIC_IN','GND','1206',0)}
  {cap('C_BUCK_OUT1','22uF',-8,-10.6,'V3V3','GND','0805')}
  {cap('C_BUCK_OUT2','22uF',-8,-12.7,'V3V3','GND','0805')}
  <diode name="D_PD" manufacturerPartNumber="B5819W" footprint="sod123" pcbX={-4.6} pcbY={3.8} connections={{anode:n('PD_VBUS'),cathode:n('LOGIC_IN')}} />
  <diode name="D_DATA" manufacturerPartNumber="B5819W" footprint="sod123" pcbX={-4.6} pcbY={1} connections={{anode:n('DATA_VBUS'),cathode:n('LOGIC_IN')}} />
  <chip name="U_DRV" {...pinProps("U_DRV")}  manufacturerPartNumber="A4988SETTR-T" pinLabels={driverPins} footprint={<A4988Footprint />} pcbX={0} pcbY={-11.5} noConnect={['NC7','NC18','NC20','NC25']} connections={{OUT1A:n('A_PLUS'),OUT1B:n('A_MINUS'),OUT2A:n('B_PLUS'),OUT2B:n('B_MINUS'),VBB1:n('PD_VBUS'),VBB2:n('PD_VBUS'),GND:n('GND'),EP:n('GND'),CP1:n('CP1'),CP2:n('CP2'),VCP:n('VCP'),VREG:n('VREG'),MS1:n('V3V3'),MS2:n('V3V3'),MS3:n('V3V3'),RESET_N:n('V3V3'),VDD:n('V3V3'),ROSC:n('GND'),STEP:n('STEP'),DIR:n('DIR'),ENABLE_N:n('ENABLE_N'),SLEEP:n('SLEEP'),REF:n('VREF'),SENSE1:n('SENSE1'),SENSE2:n('SENSE2')}} />
  {cap('C_CP','100nF',-4.2,-8.5,'CP1','CP2','0603',270)}
  {cap('C_VCP','100nF',-5.3,-11.7,'VCP','PD_VBUS','0603',270)}
  {cap('C_VREG','220nF',-5,-14.8,'VREG','GND','0603',90)}
  {cap('C_DRV_LOGIC','100nF',4.9,-10.2,'V3V3')}
  {cap('C_VM','100nF',-3,-3.9,'PD_VBUS','GND','0805',90)}
  <capacitor name="C_BULK" capacitance="47uF" maxVoltageRating={35} manufacturerPartNumber="EKMG350ELL470ME11D" footprint={<BulkFootprint />} pcbX={-13.8} pcbY={-7} connections={{pin1:n("PD_VBUS"),pin2:n("GND")}} />
  {resistor('R_SA','0.25',6.8,-12.8,'SENSE1','GND','0805',90)}
  {resistor('R_SB','0.25',-8,-14.7,'SENSE2','GND','0805')}
  {resistor('R_REF_H','36k',11.5,-5.5,'V3V3','VREF')}
  {resistor('R_REF_L','10k',11.5,-7.8,'VREF','GND')}
  {cap('C_REF','10nF',8.7,-10,'VREF')}
  {resistor('R_ENABLE','100k',-1.7,0.7,'V3V3','ENABLE_N','0402',90)}
  {resistor('R_SLEEP','100k',-6,13.5,'SLEEP','GND')}
  <chip name="J_MOTOR" {...pinProps("J_MOTOR")}  cadModel={null} pinLabels={{pin1:'A_PLUS',pin2:'A_MINUS',pin3:'B_PLUS',pin4:'B_MINUS'}} footprint={<footprint>{[-3,-1,1,3].map((x,i)=><React.Fragment key={i}><platedhole portHints={[`pin${i+1}`]} pcbX={x} pcbY={0} shape="circle" holeDiameter={0.9} outerDiameter={1.7} /></React.Fragment>)}<courtyardrect width={8} height={2.2} /></footprint>} pcbX={0} pcbY={-16} connections={{A_PLUS:n('A_PLUS'),A_MINUS:n('A_MINUS'),B_PLUS:n('B_PLUS'),B_MINUS:n('B_MINUS')}} />
  <chip name="J_DEBUG" {...pinProps("J_DEBUG")}  cadModel={null} pcbRotation={90} pinLabels={{pin1:'VDD',pin2:'GND',pin3:'SWCLK',pin4:'SWDIO',pin5:'RUN'}} footprint={<footprint>{[0,1.1,2.2,3.3,4.4].map((x,i)=><React.Fragment key={i}><smtpad portHints={[`pin${i+1}`]} pcbX={x} pcbY={0} width={.8} height={1.5} shape="rect" /></React.Fragment>)}<courtyardrect width={6} height={2} pcbX={2.2} /></footprint>} pcbX={15.5} pcbY={-8.5} connections={{VDD:n('V3V3'),GND:n('GND'),SWCLK:n('SWCLK'),SWDIO:n('SWDIO'),RUN:n('RUN')}} />
  <chip name="U_ESD" {...pinProps("U_ESD")}  manufacturerPartNumber="USBLC6-2SC6" pinLabels={{pin1:"DP1",pin2:"GND",pin3:"DM1",pin4:"DM2",pin5:"VBUS",pin6:"DP2"}} footprint={<EsdFootprint />} pcbX={5.3} pcbY={10.5} connections={{DP1:n("USB_DP"),DP2:n("USB_DP"),DM1:n("USB_DM"),DM2:n("USB_DM"),VBUS:n("DATA_VBUS"),GND:n("GND")}} />
  <diode name="D_TVS" manufacturerPartNumber="SMF18A" footprint="sod123" pcbX={-7} pcbY={15.6} connections={{anode:n("GND"),cathode:n("PD_VBUS")}} />
  <silkscreentext text="NEMA14 RP2040" pcbX={0} pcbY={15.3} fontSize={1} />
  <silkscreentext text="PD 15V" pcbX={-13.5} pcbY={-.6} fontSize={.7} />
  <silkscreentext text="USB DATA" pcbX={13} pcbY={-.6} fontSize={.7} />
  <silkscreentext text="A+ A- B+ B-" pcbX={0} pcbY={-13.7} fontSize={.65} />
  <SchematicNotes />
  </schematicsheet>
 </board>
}
