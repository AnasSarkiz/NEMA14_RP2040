import { createHash } from "node:crypto"
import { spawnSync } from "node:child_process"
import { readFileSync, writeFileSync } from "node:fs"
import { runAllChecks, checkViasInPads } from "@tscircuit/checks"
const json=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
const checks=await runAllChecks(json)
// Permit only the three explicit grounded thermal vias inside exposed pads.
const thermalNames=['U_MCU','U_DRV','U_PD','R_SA','R_SB']
const thermalCenters:Array<[number,number]>=json.filter((p:any)=>p.type==='pcb_smtpad' && p.width>1 && p.height>1 && json.some((c:any)=>c.type==='pcb_component' && c.pcb_component_id===p.pcb_component_id && json.some((s:any)=>s.type==='source_component' && s.source_component_id===c.source_component_id && thermalNames.includes(s.name)))).map((p:any)=>[p.x,p.y])
thermalCenters.push(...json.filter((p:any)=>p.type==='pcb_smtpad' && json.some((c:any)=>c.type==='pcb_component' && c.pcb_component_id===p.pcb_component_id && json.some((s:any)=>s.type==='source_component' && s.source_component_id===c.source_component_id && s.name==='C_USB')) && json.some((v:any)=>v.type==='pcb_via' && v.pcb_via_id==='service_filled_ground_cap_via' && Math.hypot(v.x-p.x,v.y-p.y)<1e-6)).map((p:any)=>[p.x,p.y] as [number,number]))
thermalCenters.push(...json.filter((p:any)=>p.type==='pcb_smtpad' && json.some((v:any)=>v.type==='pcb_via' && ['independent_star_R_SA','independent_star_R_SB','independent_filled_C_VM_ground'].includes(v.pcb_via_id) && Math.hypot(v.x-p.x,v.y-p.y)<1e-6)).map((p:any)=>[p.x,p.y] as [number,number]))
// Explicit offset GND barrel remains fully inside RP2040 exposed pad; TypeVII required.
const revisedEp=json.find((v:any)=>v.type==='pcb_via' && v.pcb_via_id==='independent_mcu_ep_ground')
const mcuEp=json.find((p:any)=>p.type==='pcb_smtpad' && p.width>1 && p.height>1 && json.some((c:any)=>c.type==='pcb_component' && c.pcb_component_id===p.pcb_component_id && json.some((s:any)=>s.type==='source_component' && s.source_component_id===c.source_component_id && s.name==='U_MCU')))
if(revisedEp && mcuEp && Math.abs(revisedEp.x-mcuEp.x-.2)<1e-6 && Math.abs(revisedEp.y-mcuEp.y)<1e-6 && revisedEp.outer_diameter===.5 && revisedEp.hole_diameter===.25)thermalCenters.push([revisedEp.x,revisedEp.y])
const ground=json.find((e:any)=>e.type==='source_net' && e.name==='GND')
const strict=json.filter((e:any)=>!(e.type==='pcb_via' && e.source_net_id===ground.source_net_id && thermalCenters.some(([x,y])=>Math.hypot(e.x-x,e.y-y)<.001))).map((e:any)=>e.type==='pcb_board'?{...e,is_via_in_pad_allowed:false}:e)
checks.push(...checkViasInPads(strict))
const renderErrors=json.filter((e:any)=>e.type.endsWith('_error'))
const errors=[...renderErrors,...checks.filter((e:any)=>e.type.endsWith('_error'))]
const unique=[...new Map(errors.map((e:any)=>[e.message,e])).values()]
for (const type of ['pcb_trace','pcb_via','pcb_port','pcb_smtpad','pcb_plated_hole','pcb_copper_pour']) {
 const ids=json.filter((e:any)=>e.type===type).map((e:any)=>e[type+'_id'])
 if(new Set(ids).size!==ids.length) unique.push({type:'validation_error',message:'Duplicate circuit record IDs: '+type})
}
const padAudit=spawnSync('/workspace/.routing-venv/bin/python',['scripts/audit-native-pad-traces.py'],{encoding:'utf8'})
if(padAudit.status!==0)unique.push({type:'validation_error',message:'Independent native pad/trace audit failed: '+padAudit.stdout+padAudit.stderr})
const warnings=checks.filter((e:any)=>e.type.endsWith('_warning'))
const traceCount=json.filter((e:any)=>e.type==='pcb_trace').length
if(traceCount===0) unique.push({type:'validation_error',message:'No routed copper was produced.'})
for(const pour of json.filter((e:any)=>e.type==='pcb_copper_pour')) {
 // runAllChecks can geometrically accept a BRep whose required discriminator
 // is absent; native Gerber serialization then silently omits that copper.
 if(pour.brep_shape && pour.shape!=='brep') unique.push({type:'validation_error',message:'BRep copper requires shape=brep for native Gerber export: '+pour.pcb_copper_pour_id})
 if(pour.covered_with_solder_mask!==true || 'is_covered_with_solder_mask' in pour) unique.push({type:'validation_error',message:'Saved copper fills must use the valid covered_with_solder_mask field: '+pour.pcb_copper_pour_id})
 const net=json.find((e:any)=>e.type==='source_net' && e.subcircuit_connectivity_map_key===pour.subcircuit_connectivity_map_key)
 if(!net || net.source_net_id!==pour.source_net_id) unique.push({type:'validation_error',message:'Copper pour source net ID/key mismatch: '+pour.pcb_copper_pour_id})
}
// Revised layout keeps inner1 a ground plane; no obsolete signal bridge is retained.
const inner1Signals=json.filter((e:any)=>e.type==='pcb_trace' && e.source_net_id!==ground.source_net_id && e.route.some((p:any)=>p.route_type==='wire' && p.layer==='inner1'))
if(inner1Signals.length) unique.push({type:'validation_error',message:'Revised inner1 must contain GND only.'})
const board=json.find((e:any)=>e.type==='pcb_board')
if(!board || board.width!==35 || board.height!==35) unique.push({type:'validation_error',message:'Expected a 35 by 35 mm PCB.'})
for (const [name,x] of [['J_PD',-7],['J_DATA',7]] as const) {
 const source=json.find((e:any)=>e.type==='source_component' && e.name===name)
 const cad=json.find((e:any)=>e.type==='cad_component' && e.source_component_id===source?.source_component_id)
 // Supplier footprint PCB rotation180 includes native CAD offset180: mouth faces +Y.
 const angle=(cad?.rotation?.z??NaN)*Math.PI/180
 const front=cad ? cad.position.y+Math.cos(angle)*(2.6-cad.model_origin_position.y) : NaN
 if(!Number.isFinite(front) || Math.abs(front-17.9)>.001 || Math.abs(cad.position.x-x)>.001 || Math.abs(Math.sin(angle))>.001 || Math.cos(angle)<.999)
  unique.push({type:'validation_error',message:name+' must have native CAD facing +Y with mouth Y17.9 and centre X'+x+'.'})
}
const usbPhysical=spawnSync('/workspace/.routing-venv/bin/python',['scripts/check-usb-head-clearance.py'],{encoding:'utf8'})
if(usbPhysical.status!==0) unique.push({type:'validation_error',message:'Exact native USB/head-circle guard failed: '+usbPhysical.stdout+usbPhysical.stderr})
const holes=json.filter((e:any)=>e.type==='pcb_hole' && e.hole_diameter===3.2)
if(holes.length!==4) unique.push({type:'validation_error',message:'Expected four 3.2 mm mounting holes.'})
const expectedHoles=[[-13,-13],[13,-13],[-14.8,13],[14.8,13]]
if(expectedHoles.some(([x,y])=>!holes.some((h:any)=>Math.abs(h.x-x)<1e-6 && Math.abs(h.y-y)<1e-6))) unique.push({type:'validation_error',message:'Carrier support hole positions must match the reviewed service revision.'})
const motorBody=spawnSync('/workspace/.routing-venv/bin/python',['scripts/check-motor-body.py'],{encoding:'utf8'})
if(motorBody.status!==0) unique.push({type:'validation_error',message:'Motor header/housing extends outside the board or lacks the required tolerance margin: '+motorBody.stdout+motorBody.stderr})
const motorSource=json.find((e:any)=>e.type==='source_component' && e.name==='J_MOTOR')
const motorPcb=json.find((e:any)=>e.type==='pcb_component' && e.source_component_id===motorSource?.source_component_id)
if(motorSource?.manufacturer_part_number!=='B4B-PH-K-S(LF)(SN)' || motorPcb?.do_not_place===true) unique.push({type:'validation_error',message:'Motor keyed header must be fitted JST B4B-PH-K-S(LF)(SN).'})
const motorPads=json.filter((e:any)=>e.type==='pcb_plated_hole' && e.pcb_component_id===motorPcb?.pcb_component_id)
if(motorPads.length!==4 || motorPads.some((e:any)=>Math.abs(e.hole_diameter-.75)>1e-6 || Math.abs(e.outer_diameter-1.6)>1e-6)) unique.push({type:'validation_error',message:'Motor land pattern must use four finished0.75mm bores and1.6mm pads per reviewed manufacturer drawing.'})
for(const [pin,netName] of [[1,'A_PLUS'],[2,'A_MINUS'],[3,'B_PLUS'],[4,'B_MINUS']] as const) {
 const p=json.find((e:any)=>e.type==='source_port' && e.source_component_id===motorSource?.source_component_id && e.pin_number===pin)
 const n=json.find((e:any)=>e.type==='source_net' && e.name===netName)
 if(!p || p.subcircuit_connectivity_map_key!==n?.subcircuit_connectivity_map_key) unique.push({type:'validation_error',message:`Motor pin${pin} must be ${netName}.`})
}
const resistance=(name:string)=>json.find((e:any)=>e.type==='source_component' && e.name===name)?.resistance
const vref=3.3*resistance('R_REF_L')/(resistance('R_REF_H')+resistance('R_REF_L')), current=vref/(8*resistance('R_SA'))
if(!Number.isFinite(current) || resistance('R_SA')!==resistance('R_SB')) unique.push({type:'validation_error',message:'Missing or mismatched phase-current setting resistors.'})
// REF leakage is guaranteed +/-3 uA. This component-only formula corner
// is NOT a qualified phase-current bound: A4988 accuracy is unspecified at VREF~0.458 V.
const rhMin=resistance('R_REF_H')*.99,rlMax=resistance('R_REF_L')*1.01
const formulaHigh=(3.6*rlMax/(rhMin+rlMax)+3e-6*rhMin*rlMax/(rhMin+rlMax))/(8*resistance('R_SA')*.99)
if(resistance('R_REF_H')!==6200 || resistance('R_REF_L')!==1000) unique.push({type:'validation_error',message:'Expected conservative 6.2k/1k reference divider; measured peak-current qualification remains required.'})
// Always-passive low-voltage monitor protects the ADC even at zero VDD.
const vmHighMin=resistance('R_VM_H')*.99,vmLowMax=resistance('R_VM_L')*1.01,vmBleedMax=resistance('R_VM_BLEED')*1.01
const vmParallelMax=vmLowMax*vmBleedMax/(vmLowMax+vmBleedMax)
const vmAdcWorst=35*vmParallelMax/(vmHighMin+vmParallelMax)+1e-6*vmBleedMax
const vmDividerInputWorst=vmAdcWorst
const vmParallelNominal=resistance('R_VM_L')*resistance('R_VM_BLEED')/(resistance('R_VM_L')+resistance('R_VM_BLEED'))
const vmAdcScaleNominal=1+resistance('R_VM_H')/vmParallelNominal
if(!Number.isFinite(vmAdcWorst) || vmAdcWorst>.3 || Math.abs(vmAdcScaleNominal-(1+100000/(10000*470/10470)))>1e-8) unique.push({type:'validation_error',message:'Passive motor monitor must stay below powered-off0.3V with1% resistors and1uA leakage at the35V arithmetic screen.'})
if(current>.4) unique.push({type:'validation_error',message:'Nominal phase current exceeds 0.4 A.'})
// Verify the RP2040 rails and required interfaces against physical pin numbers.
const sourceComponents=json.filter((e:any)=>e.type==='source_component')
const mcu=sourceComponents.find((e:any)=>e.name==='U_MCU')
if(mcu?.manufacturer_part_number!=='RP2040') unique.push({type:'validation_error',message:'Expected RP2040 in this separate project.'})
const expectedPins:Record<number,string>={1:'V3V3',8:'STEP',9:'DIR',10:'V3V3',11:'ENABLE_N',12:'SLEEP',13:'PD_GOOD',19:'GND',20:'XIN',21:'XOUT',22:'V3V3',23:'V1V1',24:'SWCLK',25:'SWDIO',26:'RUN',33:'V3V3',40:'VM_SENSE',41:'DATA_PRESENT',42:'V3V3',43:'V3V3',44:'V3V3',45:'V1V1',46:'MCU_DM',47:'MCU_DP',48:'V3V3',49:'V3V3',50:'V1V1',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS',57:'GND'}
for(const [pin,netName] of Object.entries(expectedPins)) {
 const port=json.find((e:any)=>e.type==='source_port' && e.source_component_id===mcu?.source_component_id && e.pin_number===Number(pin))
 const net=json.find((e:any)=>e.type==='source_net' && e.name===netName)
 if(!port || !net || port.subcircuit_connectivity_map_key!==net.subcircuit_connectivity_map_key) unique.push({type:'validation_error',message:`RP2040 pin ${pin} must connect to ${netName}.`})
}
for(const name of ['R_DP','R_DM']) if(sourceComponents.find((e:any)=>e.name===name)?.resistance!==27) unique.push({type:'validation_error',message:name+' must be 27 ohms.'})
for(const name of ['U_FLASH','Y_MCU','C_VREG_IN','C_VREG_OUT','C_DV23','C_DV50','U_BUCK','L_BUCK','J_BOOT','J_DEBUG']) if(!sourceComponents.some((e:any)=>e.name===name)) unique.push({type:'validation_error',message:'Missing required RP2040 support component '+name})
if(json.some((e:any)=>e.type==='pcb_component' && e.layer!=='top')) unique.push({type:'validation_error',message:'Component assembly must be top-side only.'})
if(json.some((e:any)=>e.type==='pcb_solder_paste' && e.layer!=='top')) unique.push({type:'validation_error',message:'Top assembly must not have bottom solder paste.'})
const platedHoles=json.filter((e:any)=>e.type==='pcb_plated_hole')
if(json.some((e:any)=>e.type==='pcb_solder_paste' && platedHoles.some((h:any)=>Math.hypot(h.x-e.x,h.y-e.y)<.001))) unique.push({type:'validation_error',message:'Hand-soldered through holes must not have stencil paste.'})
// Physical-pin review of motor power, PD request, protection and reset defaults.
const reviewedPhysicalPins:Record<string,Record<number,string>>={
 U_PD:{1:'PD_VDD',2:'PD_VDD',3:'PD_VDD',6:'PD_CC2',7:'PD_CC1',4:'PD_LEGACY_DATA',5:'PD_LEGACY_DATA',9:'GND',10:'PD_GOOD',11:'GND'},
 U_DRV:{1:'B_MINUS',2:'ENABLE_N',3:'GND',4:'CP1',5:'CP2',6:'VCP',8:'VREG',9:'V3V3',10:'V3V3',11:'V3V3',12:'V3V3',13:'GND',14:'SLEEP',15:'V3V3',16:'STEP',17:'VREF',18:'GND',19:'DIR',21:'A_MINUS',22:'PD_VBUS',23:'SENSE1',24:'A_PLUS',26:'B_PLUS',27:'SENSE2',28:'PD_VBUS',29:'GND'},
 U_ESD:{1:'USB_DP',2:'GND',3:'USB_DM',4:'USB_DM',5:'DATA_VBUS',6:'USB_DP'},
 Q_DATA:{1:'DATA_BASE',2:'GND',3:'DATA_PRESENT'},
 R_VM_H:{1:'PD_VBUS',2:'VM_SENSE'},R_VM_L:{1:'VM_SENSE',2:'GND'},
 R_VM_BLEED:{1:'VM_SENSE',2:'GND'},
 R_USB_SENSE_H:{1:'DATA_VBUS',2:'DATA_BASE'},R_USB_SENSE_L:{1:'V3V3',2:'DATA_PRESENT'},
 C_VM_SENSE:{1:'VM_SENSE',2:'GND'},
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
const pdSource=sourceComponents.find((e:any)=>e.name==='U_PD')
const pdSense=json.find((e:any)=>e.type==='source_port' && e.source_component_id===pdSource?.source_component_id && e.pin_number===8)
if(!pdSense?.do_not_connect) unique.push({type:'validation_error',message:'CH224K physical pin8 VBUS must be explicitly NC in documented PD-only configuration.'})
for(const [ref,expected] of [['R_ENABLE',10000],['R_SLEEP',10000],['R_VM_H',100000],['R_VM_L',10000],['R_VM_BLEED',470],['R_USB_SENSE_H',10000],['R_USB_SENSE_L',10000]] as const)
 if(resistance(ref)!==expected) unique.push({type:'validation_error',message:ref+' differs from its reviewed value.'})
for(const [reference,expected] of [['Q_DATA','MMBT3904-7-F'],['C_BULK','EEEFPV101XAP']] as const)
 if(sourceComponents.find((e:any)=>e.name===reference)?.manufacturer_part_number!==expected) unique.push({type:'validation_error',message:reference+' must use the exact reviewed native supplier part '+expected})
for(const [reference,value] of [['C_VM_SENSE',10e-9],['C_BULK',100e-6]] as const) {
 const actual=sourceComponents.find((e:any)=>e.name===reference)?.capacitance
 if(!Number.isFinite(actual) || Math.abs(actual-value)>value*1e-6) unique.push({type:'validation_error',message:reference+' differs from its reviewed capacitance.'})
}
const outerPower=spawnSync('/workspace/.routing-venv/bin/python',['scripts/audit-outer-power.py'],{encoding:'utf8'})
if(outerPower.status!==0) unique.push({type:'validation_error',message:'Actual saved outer-layer motor/PD routing policy failed: '+outerPower.stdout+outerPower.stderr})
for(const obsolete of ['U_VM_ISO','R_VM_EN','C_VM_ISO']) if(sourceComponents.some((e:any)=>e.name===obsolete)) unique.push({type:'validation_error',message:'Obsolete switched monitor must be removed: '+obsolete})
for(const [reference,expected] of [['D_TVS','SMF4L16A'],['U_ESD','USBLC6-2SC6']]) if(sourceComponents.find((e:any)=>e.name===reference)?.manufacturer_part_number!==expected) unique.push({type:'validation_error',message:'Expected exact traceable protection part: '+reference})
const report={source_sha256:createHash('sha256').update(readFileSync('artifacts/board.circuit.json')).digest('hex'),date:new Date().toISOString(),tool:'@tscircuit/checks',traceCount,currentLimitAmps:current,componentOnlyCurrentFormulaHighAmps:formulaHigh,driverCurrentAccuracyAtSelectedReferenceIsUnspecified:true,motorDividerInputAt35VWorstVolts:vmDividerInputWorst,motorAdcAt35VWorstVolts:vmAdcWorst,enabledMotorAdcScaleNominal:vmAdcScaleNominal,errors:unique,warnings,manufacturingRelease:false,releaseBlockers:['Manufacturer drawing specifies front mounting only; direct rear threads are unverified; separate front-mounted carrier requires sample fit.','Hardware has not been assembled or electrically tested.','Filled/capped exposed-pad vias and assembly process require fabricator acceptance.','A4988 accuracy at selected VREF is unspecified; measure phase current before qualification.','Footprint/rating and USB/PD bench validation remain required.','Passive monitor has a bounded below0.3V DC/stored-charge voltage at zero/partial VDD; high-frequency coupling, reset defaults, NPN levels and power handover still require prototype tests.']}
writeFileSync('artifacts/drc-report.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify({traceCount,currentLimitAmps:current,componentOnlyCurrentFormulaHighAmps:formulaHigh,driverCurrentAccuracyAtSelectedReferenceIsUnspecified:true,motorDividerInputAt35VWorstVolts:vmDividerInputWorst,motorAdcAt35VWorstVolts:vmAdcWorst,enabledMotorAdcScaleNominal:vmAdcScaleNominal,errors:unique.length,warnings:warnings.length},null,2))
for(const error of unique) console.error(error.type+': '+error.message)
if(unique.length) process.exitCode=1
