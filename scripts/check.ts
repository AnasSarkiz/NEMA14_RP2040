import { readFileSync, writeFileSync } from "node:fs"
import { runAllChecks, checkViasInPads } from "@tscircuit/checks"
const json=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
const checks=await runAllChecks(json)
// Permit only the three explicit grounded thermal vias inside exposed pads.
const thermalNames=['U_MCU','U_DRV','U_PD']
const thermalCenters:Array<[number,number]>=json.filter((p:any)=>p.type==='pcb_smtpad' && p.width>1 && p.height>1 && json.some((c:any)=>c.type==='pcb_component' && c.pcb_component_id===p.pcb_component_id && json.some((s:any)=>s.type==='source_component' && s.source_component_id===c.source_component_id && thermalNames.includes(s.name)))).map((p:any)=>[p.x,p.y])
const ground=json.find((e:any)=>e.type==='source_net' && e.name==='GND')
const strict=json.filter((e:any)=>!(e.type==='pcb_via' && e.source_net_id===ground.source_net_id && thermalCenters.some(([x,y])=>Math.hypot(e.x-x,e.y-y)<.001))).map((e:any)=>e.type==='pcb_board'?{...e,is_via_in_pad_allowed:false}:e)
checks.push(...checkViasInPads(strict))
const renderErrors=json.filter((e:any)=>e.type.endsWith('_error'))
const errors=[...renderErrors,...checks.filter((e:any)=>e.type.endsWith('_error'))]
const unique=[...new Map(errors.map((e:any)=>[e.message,e])).values()]
const warnings=checks.filter((e:any)=>e.type.endsWith('_warning'))
const traceCount=json.filter((e:any)=>e.type==='pcb_trace').length
if(traceCount===0) unique.push({type:'validation_error',message:'No routed copper was produced.'})
const board=json.find((e:any)=>e.type==='pcb_board')
if(!board || board.width!==35 || board.height!==35) unique.push({type:'validation_error',message:'Expected a 35 by 35 mm PCB.'})
const usbMouths:Array<{name:string,x:number,y:number}> = []
for (const name of ['J_PD','J_DATA']) {
 const source=json.find((e:any)=>e.type==='source_component' && e.name===name)
 const cad=json.find((e:any)=>e.type==='cad_component' && e.source_component_id===source?.source_component_id)
 const angle=(cad?.rotation?.z??NaN)*Math.PI/180
 const offset=cad ? 2.6-cad.model_origin_position.y : NaN
 const x=cad ? cad.position.x-Math.sin(angle)*offset : NaN
 const y=cad ? cad.position.y+Math.cos(angle)*offset : NaN
 const expectedX=name==='J_PD'?-6.2:6.2
 if(!Number.isFinite(y) || Math.abs(y-17.5)>.001 || Math.abs(x-expectedX)>.001 || Math.abs(Math.sin(angle))>.0001 || Math.cos(angle)<.9999)
  unique.push({type:'validation_error',message:name+' must face +Y with its native mouth at the Y=17.5 mm edge and reviewed X position.'})
 usbMouths.push({name,x,y})
}
if(usbMouths.length!==2 || Math.abs(usbMouths[1].x-usbMouths[0].x-12.4)>.001)
 unique.push({type:'validation_error',message:'Same-edge USB mouths must have 12.4 mm centre pitch for two 12 mm plug envelopes.'})
const mountingKeepouts=json.filter((e:any)=>e.type==='pcb_keepout')
const expectedLayers=board?.num_layers===4?['top','inner1','inner2','bottom']:['top','bottom']
if(mountingKeepouts.length!==4 || mountingKeepouts.some((e:any)=>e.shape!=='circle' || Math.abs(e.radius-2.2)>.00001 || ![-13,13].includes(e.center.x) || ![-13,13].includes(e.center.y) || expectedLayers.some(l=>!e.layers.includes(l))))
 unique.push({type:'validation_error',message:'All four mounts require circular Ø4.4 mm head envelopes on every copper layer; DIN 920 M3 Ø4 mm heads are mandatory.'})

if(board?.num_layers!==4) unique.push({type:'validation_error',message:'Expected four copper layers in the RP2040 board.'})
for(const via of json.filter((e:any)=>e.type==='pcb_via')) {
 if(via.hole_diameter<board.min_via_hole_diameter || via.outer_diameter<board.min_via_pad_diameter) unique.push({type:'validation_error',message:'Via violates the declared minimum pad/drill diameter: '+via.pcb_via_id})
}
const inner1LocalNets=new Set(['QSPI_SCLK','QSPI_SD0','QSPI_SD1','QSPI_SD2','QSPI_SD3','QSPI_SS','XIN','XOUT','XTAL_OUT','RUN','SWCLK','SWDIO','USB_DP','USB_DM','MCU_DP','MCU_DM','DIR','STATUS_B_K','LED_B','PWR_LED_A','V3V3','DATA_VBUS','TEMP_SDA','TEMP_SCL','GND'])
for(const trace of json.filter((e:any)=>e.type==='pcb_trace' && e.route.some((p:any)=>p.layer==='inner1'))) {
 const net=json.find((e:any)=>e.type==='source_net' && e.subcircuit_connectivity_map_key===trace.subcircuit_connectivity_map_key)
 if(!inner1LocalNets.has(net?.name)) unique.push({type:'validation_error',message:'Unreviewed net on inner1: '+trace.pcb_trace_id})
}
const holes=json.filter((e:any)=>e.type==='pcb_hole' && e.hole_diameter===3.2)
const mountCoordinates=new Set(holes.map((e:{x:number,y:number})=>`${e.x},${e.y}`))
if(holes.length!==4 || mountCoordinates.size!==4 || [-13,13].some(x=>[-13,13].some(y=>!mountCoordinates.has(`${x},${y}`))))
 unique.push({type:'validation_error',message:'Mounting holes must be exactly the four (±13, ±13) mm coordinates, Ø3.2 mm.'})
const mountHoles=json.filter((e:{type:string,pcb_component_id?:string|null})=>e.type==='pcb_hole' && !e.pcb_component_id)
if(mountHoles.length!==4) unique.push({type:'validation_error',message:'Expected exactly four board mounting holes, excluding connector alignment holes.'})
const resistance=(name:string)=>json.find((e:any)=>e.type==='source_component' && e.name===name)?.resistance
const vref=3.3*resistance('R_REF_L')/(resistance('R_REF_H')+resistance('R_REF_L')), current=vref/(8*resistance('R_SA'))
if(!Number.isFinite(current) || resistance('R_SA')!==resistance('R_SB')) unique.push({type:'validation_error',message:'Missing or mismatched phase-current setting resistors.'})
const worstCurrent=3.465*(resistance('R_REF_L')*1.01)/(resistance('R_REF_H')*.99+resistance('R_REF_L')*1.01)/(8*resistance('R_SA')*.99)*1.05
if(worstCurrent>.4) unique.push({type:'validation_error',message:'Estimated tolerance-bound phase current exceeds 0.4 A.'})
const vmAdcWorst=35*(resistance('R_VM_L')*1.01)/(resistance('R_VM_H')*.99+resistance('R_VM_L')*1.01)
if(!Number.isFinite(vmAdcWorst) || vmAdcWorst>3.3) unique.push({type:'validation_error',message:'Motor voltage divider exceeds 3.3 V at the 35 V review envelope.'})
if(current>.4) unique.push({type:'validation_error',message:'Nominal phase current exceeds 0.4 A.'})
// Verify the RP2040 rails and required interfaces against physical pin numbers.
const sourceComponents=json.filter((e:any)=>e.type==='source_component')
const mcu=sourceComponents.find((e:any)=>e.name==='U_MCU')
if(mcu?.manufacturer_part_number!=='RP2040') unique.push({type:'validation_error',message:'Expected RP2040 in this separate project.'})
const expectedPins:Record<number,string>={1:'V3V3',10:'V3V3',19:'GND',20:'XIN',21:'XOUT',22:'V3V3',23:'V1V1',24:'SWCLK',25:'SWDIO',26:'RUN',33:'V3V3',40:'VM_SENSE',41:'DATA_PRESENT',42:'V3V3',43:'V3V3',44:'V3V3',45:'V1V1',46:'MCU_DM',47:'MCU_DP',48:'V3V3',49:'V3V3',50:'V1V1',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS',57:'GND'}
for(const [pin,netName] of Object.entries(expectedPins)) {
 const port=json.find((e:any)=>e.type==='source_port' && e.source_component_id===mcu?.source_component_id && e.pin_number===Number(pin))
 const net=json.find((e:any)=>e.type==='source_net' && e.name===netName)
 if(!port || !net || port.subcircuit_connectivity_map_key!==net.subcircuit_connectivity_map_key) unique.push({type:'validation_error',message:`RP2040 pin ${pin} must connect to ${netName}.`})
}
for(const name of ['R_DP','R_DM']) if(sourceComponents.find((e:any)=>e.name===name)?.resistance!==27) unique.push({type:'validation_error',message:name+' must be 27 ohms.'})
for(const name of ['U_FLASH','Y_MCU','C_VREG_IN','C_VREG_OUT','C_DV23','C_DV50','U_BUCK','L_BUCK','J_BOOT','J_DEBUG']) if(!sourceComponents.some((e:any)=>e.name===name)) unique.push({type:'validation_error',message:'Missing required RP2040 support component '+name})
const bottomReferences=new Set(['C_DV50','C_IO49','R_XOUT','C_XOUT','J_DEBUG','R_TEMP_SDA'])
for(const component of json.filter((e:any)=>e.type==='pcb_component')) {
 const source=json.find((e:any)=>e.type==='source_component' && e.source_component_id===component.source_component_id)
 if(component.layer!==(bottomReferences.has(source?.name)?'bottom':'top')) unique.push({type:'validation_error',message:'Unreviewed component assembly side: '+source?.name})
}
for(const paste of json.filter((e:any)=>e.type==='pcb_solder_paste')) {
 const component=json.find((e:any)=>e.type==='pcb_component' && e.pcb_component_id===paste.pcb_component_id)
 if(component && paste.layer!==component.layer) unique.push({type:'validation_error',message:'Paste is on the wrong component assembly side: '+paste.pcb_solder_paste_id})
}
const platedHoles=json.filter((e:any)=>e.type==='pcb_plated_hole')
if(json.some((e:any)=>e.type==='pcb_solder_paste' && platedHoles.some((h:any)=>Math.hypot(h.x-e.x,h.y-e.y)<.001))) unique.push({type:'validation_error',message:'Hand-soldered through holes must not have stencil paste.'})
// Physical-pin review of motor power, PD request, protection and reset defaults.
const reviewedPhysicalPins:Record<string,Record<number,string>>={
 U_PD:{1:'PD_VDD',2:'PD_VDD',3:'PD_VDD',6:'PD_CC2',7:'PD_CC1',8:'PD_VBUS',9:'GND',10:'PD_GOOD',11:'GND'},
 U_DRV:{1:'B_MINUS',2:'ENABLE_N',3:'GND',4:'CP1',5:'CP2',6:'VCP',8:'VREG',9:'V3V3',10:'V3V3',11:'V3V3',12:'V3V3',13:'GND',14:'SLEEP',15:'V3V3',16:'STEP',17:'VREF',18:'GND',19:'DIR',21:'A_MINUS',22:'PD_VBUS',23:'SENSE1',24:'A_PLUS',26:'B_PLUS',27:'SENSE2',28:'PD_VBUS',29:'GND'},
 U_ESD:{1:'USB_DP',2:'GND',3:'USB_DM',4:'USB_DM',5:'DATA_VBUS',6:'USB_DP'},
}
reviewedPhysicalPins.U_BUCK={1:'V3V3',2:'LOGIC_IN',3:'LOGIC_IN',4:'GND',5:'BUCK_SW',6:'BUCK_BST'}
for(const [reference,pins] of Object.entries(reviewedPhysicalPins)) {
 const component=json.find((e:any)=>e.type==='source_component' && e.name===reference)
 for(const [pin,netName] of Object.entries(pins)) {
  const port=json.find((e:any)=>e.type==='source_port' && e.source_component_id===component?.source_component_id && e.pin_number===Number(pin))
  const net=json.find((e:any)=>e.type==='source_net' && e.name===netName)
  if(!port || !net || port.subcircuit_connectivity_map_key!==net.subcircuit_connectivity_map_key) unique.push({type:'validation_error',message:`${reference} physical pin ${pin} must connect to ${netName}.`})
 }
}
for(const [ref,expected] of [['R_ENABLE',100000],['R_SLEEP',100000],['R_VM_H',100000],['R_VM_L',10000]] as const)
 if(resistance(ref)!==expected) unique.push({type:'validation_error',message:ref+' differs from its reviewed value.'})
// The motor interface must be a fitted JST PH part, with its native CAD model and reviewed coil order.
const motorConnector=json.find((e:any)=>e.type==='source_component' && e.name==='J_MOTOR')
if(motorConnector?.manufacturer_part_number!=='B4B-PH-K-S(LF)(SN)' || motorConnector?.supplier_part_numbers?.jlcpcb?.[0]!=='C131334')
 unique.push({type:'validation_error',message:'J_MOTOR must be the fitted 4-pin JST PH B4B-PH-K-S(LF)(SN), C131334.'})
if(!json.some((e:any)=>e.type==='cad_component' && e.source_component_id===motorConnector?.source_component_id && e.model_step_url && e.model_obj_url))
 unique.push({type:'validation_error',message:'J_MOTOR requires the actual supplier STEP and OBJ models.'})
for(const [i,name] of ['A_PLUS','A_MINUS','B_PLUS','B_MINUS'].entries()) {
 const port=json.find((e:any)=>e.type==='source_port' && e.source_component_id===motorConnector?.source_component_id && e.pin_number===i+1)
 const net=json.find((e:any)=>e.type==='source_net' && e.name===name)
 if(!port || !net || port.subcircuit_connectivity_map_key!==net.subcircuit_connectivity_map_key) unique.push({type:'validation_error',message:`J_MOTOR pin ${i+1} must connect to ${name}.`})
}
const report={date:new Date().toISOString(),tool:'@tscircuit/checks',traceCount,currentLimitAmps:current,currentLimitEngineeringBudgetAmps:worstCurrent,currentLimitBudgetIsNotQualified:true,motorAdcAt35VWorstVolts:vmAdcWorst,errors:unique,warnings,manufacturingRelease:false,releaseBlockers:['Manufacturer drawing specifies front mounting only; rear adapter fit is unverified.','Hardware has not been assembled or electrically tested.','Footprint/rating and USB/PD bench validation remain required.']}
writeFileSync('artifacts/drc-report.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify({traceCount,currentLimitAmps:current,currentLimitEngineeringBudgetAmps:worstCurrent,currentLimitBudgetIsNotQualified:true,motorAdcAt35VWorstVolts:vmAdcWorst,errors:unique.length,warnings:warnings.length},null,2))
for(const error of unique) console.error(error.type+': '+error.message)
if(unique.length) process.exitCode=1
