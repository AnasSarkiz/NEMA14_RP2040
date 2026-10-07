import { readFileSync, writeFileSync } from "node:fs"
import { runAllChecks, checkViasInPads } from "@tscircuit/checks"
const json=JSON.parse(readFileSync('artifacts/board.circuit.json','utf8'))
const checks=await runAllChecks(json)
// Permit only the three explicit grounded thermal vias inside exposed pads.
const thermalCenters=[[3.4,0],[0,-11.5],[-3.4,8.2]]
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
for (const [name,edge] of [['J_PD',-17.5],['J_DATA',17.5]] as const) {
 const source=json.find((e:any)=>e.type==='source_component' && e.name===name)
 const component=json.find((e:any)=>e.type==='pcb_component' && e.source_component_id===source?.source_component_id)
 const points=json.filter((e:any)=>e.type==='pcb_fabrication_note_path' && e.pcb_component_id===component?.pcb_component_id).flatMap((e:any)=>e.route)
 const front=points.length ? (edge<0?Math.min(...points.map((p:any)=>p.x)):Math.max(...points.map((p:any)=>p.x))) : NaN
 if(!Number.isFinite(front) || Math.abs(front-edge)>.001) unique.push({type:'validation_error',message:name+' opening is not flush with the board edge.'})
}
if(board?.num_layers!==4) unique.push({type:'validation_error',message:'Expected four copper layers in the RP2040 board.'})
for(const via of json.filter((e:any)=>e.type==='pcb_via')) {
 if(via.hole_diameter<board.min_via_hole_diameter || via.outer_diameter<board.min_via_pad_diameter) unique.push({type:'validation_error',message:'Via violates the declared minimum pad/drill diameter: '+via.pcb_via_id})
}
if(json.some((e:any)=>e.type==='pcb_trace' && e.route.some((p:any)=>p.layer==='inner1'))) unique.push({type:'validation_error',message:'Inner1 is reserved for ground.'})
const holes=json.filter((e:any)=>e.type==='pcb_hole' && e.hole_diameter===3.2)
if(holes.length!==4) unique.push({type:'validation_error',message:'Expected four 3.2 mm mounting holes.'})
const vref=3.3*10000/(36000+10000), current=vref/(8*.25)
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
if(json.some((e:any)=>e.type==='pcb_component' && e.layer!=='top')) unique.push({type:'validation_error',message:'Component assembly must be top-side only.'})
if(json.some((e:any)=>e.type==='pcb_solder_paste' && e.layer!=='top')) unique.push({type:'validation_error',message:'Top assembly must not have bottom solder paste.'})
const platedHoles=json.filter((e:any)=>e.type==='pcb_plated_hole')
if(json.some((e:any)=>e.type==='pcb_solder_paste' && platedHoles.some((h:any)=>Math.hypot(h.x-e.x,h.y-e.y)<.001))) unique.push({type:'validation_error',message:'Hand-soldered through holes must not have stencil paste.'})
const report={date:new Date().toISOString(),tool:'@tscircuit/checks',traceCount,currentLimitAmps:current,errors:unique,warnings,manufacturingRelease:false,releaseBlockers:['Manufacturer drawing specifies front mounting only; rear adapter fit is unverified.','Hardware has not been assembled or electrically tested.','Footprint/rating and USB/PD bench validation remain required.']}
writeFileSync('artifacts/drc-report.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify({traceCount,currentLimitAmps:current,errors:unique.length,warnings:warnings.length},null,2))
for(const error of unique) console.error(error.type+': '+error.message)
if(unique.length) process.exitCode=1
