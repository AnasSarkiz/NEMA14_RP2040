/** Functional A4 presentation of the native electrical graph.
 * Every non-schematic record and physical pin identity is retained verbatim.
 * Named nets link functional sections; bypass banks and local series networks
 * use actual native schematic wires. No PCB routing is generated here.
 */
type Position = [number, number]
type Section = { title:string; bounds:[number,number,number,number]; parts:Record<string,Position>; note?:[number,number,string]; banks?:string[][] }
type Page = { name:string; sections:Section[] }
export function prepareSchematic(json:any[]) {
 const template=json.find(e=>e.type==='schematic_sheet')
 if(!template)throw new Error('An explicit A4 schematic sheet is required')
 const source=new Map<string,any>(json.filter(e=>e.type==='source_component').map(e=>[e.source_component_id,e]))
 const sourcePorts=new Map<string,any>(json.filter(e=>e.type==='source_port').map(e=>[e.source_port_id,e]))
 const nets=new Map<string,any>(json.filter(e=>e.type==='source_net').map(e=>[e.subcircuit_connectivity_map_key,e]))
 const byName=new Map<string,any>(json.filter(e=>e.type==='schematic_component').map(e=>[source.get(e.source_component_id).name,e]))
 const isRp=source.get(byName.get('U_MCU').source_component_id).manufacturer_part_number==='RP2040'
 const design=isRp?'NEMA14 RP2040':'NEMA14 CH32X035G8U6'
 const pinGroups=new Map<string,any[]>()
 for(const p of sourcePorts.values())if(p.subcircuit_connectivity_map_key)pinGroups.set(p.subcircuit_connectivity_map_key,[...(pinGroups.get(p.subcircuit_connectivity_map_key)??[]),p])
 for(const [key,ports]of pinGroups)if(!nets.has(key)&&ports.length>1)nets.set(key,{name:ports.find(p=>!/^pin\d/.test(p.name))?.name??ports[0].name,subcircuit_connectivity_map_key:key})
 const pages:Page[]=[{name:'USB-C PD & Logic Power',sections:[
  {title:'15 V USB-C PD negotiation',bounds:[-15,2,1.0,8.8],parts:{J_PD:[-12.1,5.4],U_PD:[-4.2,5.4],R_PD:[-.8,7],C_PD:[-.8,4.8],R_PG:[1,2.7]},note:[-14.8,.2,'U_PD / CH224K requests 15 V (CFG1=0, CFG2=CFG3=1).\nOpen-drain PG is active low. DP/DM short: PD-only mode.\nR_PD + C_PD supply/filter the negotiation IC.']},
  {title:'USB / PD diode OR',bounds:[2.6,15,3.2,8.8],parts:{D_PD:[7,6.8],D_DATA:[7,4.7]},note:[3,3.4,'Schottky diodes accept either supply and block crossfeed.']},
  isRp?{title:'3.3 V buck supply',bounds:[2.6,15,-5.6,2.5],parts:{U_BUCK:[6,-.3],L_BUCK:[11,-.3],C_BOOTSTRAP:[9,1.2],C_BUCK_IN:[3.9,-3.1],C_BUCK_OUT1:[10.4,-3.1],C_BUCK_OUT2:[12,-3.1]},banks:[['C_BUCK_OUT1','C_BUCK_OUT2']],note:[3,-6.1,'U_BUCK / AP63203 converts LOGIC_IN to 3.3 V.\n4.7 uH L_BUCK and output capacitors filter the switching node.\nC_BOOTSTRAP supports the high-side gate driver.']}:
  {title:'3.3 V logic regulator',bounds:[2.6,15,-4.7,2.5],parts:{U_LDO:[8,-.2],C_LDO_IN:[3.8,-2.9],C_LDO_OUT:[12,-2.9]},note:[3,-5.4,'U_LDO / HT7533-1 supplies the low-current CH32 logic.\n30 V operating input, 33 V absolute maximum.\nInput spikes and mounted thermal margins remain bench gates.']}
 ]},{name:isRp?'RP2040 & USB Control':'CH32 & USB Control',sections:[
  {title:isRp?'Application MCU / physical pin map':'Application MCU & local bypass',bounds:[-15,-5.7,isRp?-7.4:-7.4,8.8],parts:{U_MCU:[-10.1,isRp?.4:2.3],...(isRp?{R_RUN:[-10.5,-6.3]}:{C_MCU:[-12.3,-3.2],C_LOGIC:[-10.7,-3.2]})},banks:isRp?[]:[['C_MCU','C_LOGIC']],note:[-14.8,-8.1,isRp?'U_MCU / RP2040 generates STEP/DIR and reads power status.\nInternal regulator: 1.1 V core. Flash/clock/bypass: next sheet.': 'U_MCU / CH32X035 controls USB and STEP/DIR.\nInternal clock avoids an external crystal.']},
  {title:'Computer USB-C & ESD protection',bounds:[-5,15,0,8.8],parts:{J_DATA:[11.1,5.4],U_ESD:[3.7,5.4],R_CC1:[10.1,1.3],R_CC2:[13.3,1.3],...(isRp?{R_DM:[-1.1,5.9],R_DP:[-1.1,3.8]}:{})},banks:[['R_CC1','R_CC2']],note:[-4.8,.2,'U_ESD / USBLC6 protects D+/D-. R_CC1/2 identify a USB sink.']},
  {title:'Host VBUS detection',bounds:[1.8,15,-5.5,-1.0],parts:{Q_DATA:[7.8,-3.4],R_USB_SENSE_H:[2.2,-3.4],R_USB_SENSE_L:[13.1,-3.4]},note:[2,-6,'Q_DATA / MMBT3904 senses host 5 V without a direct GPIO feed.\nDATA_PRESENT LOW means host attached.']},
  {title:'Programming & recovery',bounds:[-5,1.2,-8.8,-1.0],parts:isRp?{J_DEBUG:[-1.8,-6.5]}:{J_DEBUG:[-2,-2.8],R_USB_BOOT:[-3.9,-5.8],J_BOOT:[-.9,-7]},note:[isRp?-4.8:-4.8,isRp?-2.0:-4.3,isRp?'SWD / RUN pads allow debug and reset.\nUSB ROM boot: BOOT pads on next sheet.':'WCH debug pads and USB boot strap.\nUse documented recovery sequence.']}
 ]}]
 if(isRp)pages.push({name:'Flash, Clock & MCU Supply',sections:[
  {title:'External QSPI firmware & ROM recovery',bounds:[-15,0,1.2,8.8],parts:{U_FLASH:[-9,5.6],C_FLASH:[-13.2,5.4],R_FLASH_CS:[-5.4,6.9],R_BOOT:[-4.4,3.8],J_BOOT:[-1.7,5.4]},note:[-14.8,1.6,'U_FLASH / GD25Q16 provides 2 MB firmware storage.\nRP2040 has no internal flash. BOOT shorts QSPI_SS via R_BOOT\nto ground during reset, entering the ROM USB bootloader.']},
  {title:'12 MHz USB clock reference',bounds:[.6,15,1.2,8.8],parts:{Y_MCU:[8,5.6],R_XOUT:[3.3,5.6],C_XIN:[5.3,3.1],C_XOUT:[11.1,3.1]},note:[.8,1.6,'Y_MCU / ABM8 is the USB clock reference.\nLoad capacitors support oscillation; R_XOUT limits crystal drive.']},
  {title:'MCU power pins / local bypass',bounds:[-15,15,-8.8,.4],parts:{C_IO1:[-13,-2.5],C_IO10:[-11.4,-2.5],C_IO22:[-9.8,-2.5],C_IO33:[-8.2,-2.5],C_IO42:[-6.6,-2.5],C_IO49:[-5,-2.5],C_USB:[-3.4,-2.5],C_ADC:[-1.8,-2.5],C_VREG_IN:[-.2,-2.5],C_DV23:[-10.5,-6.2],C_DV50:[-8.9,-6.2],C_VREG_OUT:[-7.3,-6.2]},banks:[['C_IO1','C_IO10','C_IO22','C_IO33','C_IO42','C_IO49','C_USB','C_ADC','C_VREG_IN'],['C_DV23','C_DV50','C_VREG_OUT']],note:[2.5,-6,'Each capacitor is a distinct fitted part.\nIO pin numbers appear in references.\nVREG_OUT feeds V1V1; no external 1.1 V source.' ]}
 ]})
 pages.push({name:'Motor Driver & Voltage Monitor',sections:[
  {title:'A4988 / bipolar winding driver',bounds:[-15,-5.7,-1.1,8.8],parts:{U_DRV:[-10,3.6]}},
  {title:'Keyed motor output & current shunts',bounds:[-5,2.6,.1,8.8],parts:{J_MOTOR:[-1.2,6.7],R_SA:[-2.6,2.1],R_SB:[.7,2.1]},banks:[['R_SA','R_SB']],note:[-4.8,.5,'1 Black A+   2 Green A-\n3 Red B+     4 Blue B-']},
  {title:'Current reference & safe defaults',bounds:[3.2,15,.1,8.8],parts:{R_REF_H:[5.2,6.2],R_REF_L:[5.2,3.7],C_REF:[8.2,3.7],R_ENABLE:[11,6.2],R_SLEEP:[14,6.2],C_DRV_LOGIC:[12.1,2.1]},note:[3.4,.5,'3.9k / 1k VREF and 0.24 ohm shunts: 0.351 A nominal.\nENABLE pull-up / SLEEP pull-down keep the driver off.' ]},
  {title:'Charge pump, motor decoupling & clamp',bounds:[-15,.1,-7.0,-1.8],parts:{C_CP:[-13,-3.6],C_VCP:[-9.9,-3.6],C_VREG:[-6.7,-3.6],C_VM:[-13,-6],C_VM2:[-11.4,-6],C_BULK:[-9.6,-6],D_TVS:[-2.3,-4.8]},banks:[['C_VM','C_VM2','C_BULK']],note:[-14.8,-7.7,'U_DRV regulates both windings at fixed 1/16 microsteps.\nC_CP / C_VCP / C_VREG support the internal driver rails.\nBulk capacitance and TVS limit transients; regeneration needs bench tests.']},
  {title:'Motor-voltage monitor / power-off isolation',bounds:[.8,15,-8.8,-1.0],parts:{R_VM_H:[2.1,-3.3],R_VM_L:[2.1,-5.7],U_VM_ISO:[7,-4.2],R_VM_EN:[14,-2.6],C_VM_ISO:[11,-3.3],R_VM_BLEED:[9.8,-7],C_VM_SENSE:[13,-7]},note:[1,-8.2,'U_VM_ISO / SN74CBTLV1G125 blocks ADC backfeed when off.\nOE pull-up defaults off; MCU enables, waits 0.5 ms, then samples VM/21.' ]}
 ]})
 const out=json.filter(e=>!e.type.startsWith('schematic_'));let seq=0
 const text=(sheet:string,value:string,x:number,y:number,size=.21,anchor='left',component?:string)=>out.push({type:'schematic_text',schematic_text_id:`functional_text_${seq++}`,schematic_sheet_id:sheet,text:value,position:{x,y},anchor,rotation:0,font_size:size,color:'#006464',...(component?{schematic_component_id:component}:{})})
 const newPorts=new Map<string,any>();const connected=new Set<string>();const placed=new Set<string>();const pageByRef=new Map<string,string>()
 const trace=(sheet:string,pts:{x:number;y:number}[],key:string,junctions:{x:number;y:number}[]=[])=>out.push({type:'schematic_trace',schematic_trace_id:`functional_trace_${seq++}`,edges:pts.slice(1).map((to,i)=>({from:pts[i],to})),junctions,schematic_sheet_id:sheet,subcircuit_connectivity_map_key:key,source_trace_id:json.find(e=>e.type==='source_trace'&&e.subcircuit_connectivity_map_key===key)?.source_trace_id})
 const netOf=(p:any)=>nets.get(sourcePorts.get(p.source_port_id)?.subcircuit_connectivity_map_key)
 const label=(sheet:string,p:any,end:any,side:string)=>{const net=netOf(p);if(net)out.push({type:'schematic_net_label',schematic_net_label_id:`functional_net_${seq++}`,source_net_id:net.source_net_id,text:net.name,anchor_position:end,center:end,anchor_side:side,schematic_sheet_id:sheet})}
 const widths:Record<string,number>={U_MCU:isRp?2.7:3.27,U_DRV:2.51,J_PD:2.055,J_DATA:2.055,U_PD:1.94,U_FLASH:1.75,J_BOOT:1.2,J_DEBUG:isRp?2.12:1.75,Y_MCU:1.96,U_BUCK:1.75,U_LDO:1.84,J_MOTOR:2.51,U_ESD:1.84,U_VM_ISO:1.865,Q_DATA:1.69,D_TVS:1.38}
 pages.forEach((page,i)=>{
  const sheet=`schematic_sheet_${i}`
  out.push({...template,schematic_sheet_id:sheet,name:page.name,display_name:page.name,sheet_index:i,sheet_size:'a4',sheet_width:297,sheet_height:210,center:{x:0,y:0}})
  text(sheet,`${design} | ${page.name}`,-15,10,.32)
  text(sheet,`A4 landscape  |  ${i+1} / ${pages.length}  |  Named nets connect across sheets  |  NC = intentionally unused pin`,-15,-9.8,.19)
  for(const section of page.sections){
   const [x0,x1,y0,y1]=section.bounds
   const groupId=`functional_section_${seq++}`
   out.push({type:"schematic_group",schematic_group_id:groupId,schematic_sheet_id:sheet,source_group_id:json.find(e=>e.type==='source_group').source_group_id,center:{x:(x0+x1)/2,y:(y0+y1)/2},width:x1-x0,height:y1-y0,schematic_component_ids:Object.keys(section.parts).map(n=>byName.get(n).schematic_component_id),show_as_schematic_box:false,name:section.title})
   out.push({type:'schematic_rect',schematic_rect_id:`functional_frame_${seq++}`,schematic_sheet_id:sheet,center:{x:(x0+x1)/2,y:(y0+y1)/2},width:x1-x0,height:y1-y0,rotation:0,stroke_width:.012,color:'#91a5ab',is_filled:false,is_dashed:true})
   text(sheet,section.title,x0+.18,y1-.28,.24)
   if(section.note)text(sheet,section.note[2],section.note[0],section.note[1],.185)
   for(const [name,pos]of Object.entries(section.parts)){
    const old=byName.get(name);if(!old)throw new Error('Unknown schematic component '+name);if(placed.has(name))throw new Error('Repeated component '+name)
    placed.add(name);pageByRef.set(name,sheet);const s=source.get(old.source_component_id);const center={x:pos[0],y:pos[1]}
    const ports=json.filter(e=>e.type==='schematic_port'&&e.schematic_component_id===old.schematic_component_id).sort((a,b)=>a.pin_number-b.pin_number)
    const boxed=!old.symbol_name;const half=Math.ceil(ports.length/2),spacing=.4
    const horizontalInductor=name==='L_BUCK'
    const verticalBox=name==='J_BOOT'||name==='D_TVS'
    const verticalPd=name==='R_PD'
    const size=verticalPd?(old.symbol_name==='boxresistor_down'?old.size:{width:old.size.height,height:old.size.width}):horizontalInductor?(old.symbol_name==='inductor_right'?old.size:{width:old.size.height,height:old.size.width}):boxed?{width:widths[name]??2.8,height:verticalBox?1.8:Math.max(1.2,half*spacing+.7)}:old.size
    const c={...old,center,size,schematic_sheet_id:sheet,pin_spacing:spacing};c.schematic_group_id=groupId;if(horizontalInductor)c.symbol_name='inductor_right';if(verticalPd)c.symbol_name='boxresistor_down';out.push(c)
    if(boxed){text(sheet,name,center.x-size.width/2,center.y+size.height/2+.35,.24,'left',c.schematic_component_id);text(sheet,s.manufacturer_part_number??'PCB recovery / debug pads',center.x-size.width/2,center.y-size.height/2-.34,.18,'left',c.schematic_component_id)}
    else if(!c.symbol_display_value)text(sheet,s.manufacturer_part_number??name,center.x+.7,center.y-.3,.17,'left',c.schematic_component_id)
    ports.forEach((oldPort,j)=>{
     const left=j<half,row=left?j:j-half
     const pinCenter=verticalPd?{x:center.x,y:center.y+(j===0?1:-1)*size.height/2}:verticalBox?{x:center.x,y:center.y+(name==='D_TVS'?(j===0?-1:1):(j===0?1:-1))*(size.height/2+.35)}:horizontalInductor?{x:center.x+(j===0?-1:1)*size.width/2,y:center.y}:boxed?{x:center.x+(left?-1:1)*(size.width/2+.35),y:center.y+(half-1)*spacing/2-row*spacing}:{x:center.x+oldPort.center.x-old.center.x,y:center.y+oldPort.center.y-old.center.y}
     const direction=verticalPd?(j===0?'up':'down'):verticalBox?(name==='D_TVS'?(j===0?'down':'up'):(j===0?'up':'down')):horizontalInductor?(j===0?'left':'right'):boxed?(left?'left':'right'):oldPort.facing_direction
     const p={...oldPort,center:pinCenter,schematic_sheet_id:sheet,display_pin_label_font_size:.17,...(boxed||horizontalInductor||verticalPd?{side_of_component:direction==='up'?'top':direction==='down'?'bottom':direction,facing_direction:direction,distance_from_component_edge:.35}:{})}
     newPorts.set(`${name}.${p.pin_number}`,p);out.push(p)
    })
   }
   // Actual wired bypass banks: connect only ports with exactly equal native net keys.
   for(const bank of section.banks??[]){
    for(const pin of [1,2]){
     const ps=bank.map(name=>newPorts.get(`${name}.${pin}`));const keys=ps.map(p=>sourcePorts.get(p.source_port_id)?.subcircuit_connectivity_map_key)
     if(!keys[0]||!keys.every(k=>k===keys[0]))continue
     const y=ps[0].center.y+(pin===1?.52:-.52)
     for(const p of ps){trace(sheet,[p.center,{x:p.center.x,y}],keys[0]);connected.add(p.schematic_port_id)}
     const xMin=Math.min(...ps.map(p=>p.center.x))-.6,xMax=Math.max(...ps.map(p=>p.center.x))
     trace(sheet,[{x:xMin,y},{x:xMax,y}],keys[0],ps.map(p=>({x:p.center.x,y})));label(sheet,ps[0],{x:xMin,y},'right')
    }
   }
  }
 })
 // Local series chains are wired, while inter-section signals keep named net labels.
 const wirePair=(a:string,b:string)=>{
  const pa=newPorts.get(a),pb=newPorts.get(b);if(!pa||!pb)return
  const ka=sourcePorts.get(pa.source_port_id)?.subcircuit_connectivity_map_key,kb=sourcePorts.get(pb.source_port_id)?.subcircuit_connectivity_map_key
  if(!ka||ka!==kb)throw new Error('Local wire would change native net: '+a+' / '+b)
  const sheet=pa.schematic_sheet_id;if(sheet!==pb.schematic_sheet_id)throw new Error('Local wire spans sheets')
  trace(sheet,[pa.center,{x:pa.center.x,y:pb.center.y},pb.center],ka);connected.add(pa.schematic_port_id);connected.add(pb.schematic_port_id)
  // Keep the shared net visible even when both pin stubs become a wire.
  const end={x:pa.center.x,y:(pa.center.y+pb.center.y)/2};label(sheet,pa,end,'left')
 }
 wirePair('R_PD.2','C_PD.1');wirePair('R_REF_H.2','R_REF_L.1');wirePair('R_VM_H.2','R_VM_L.1')
 for(const p of newPorts.values())if(!connected.has(p.schematic_port_id)){
  const d=p.facing_direction,v=d==='left'?{x:-1,y:0}:d==='right'?{x:1,y:0}:d==='up'?{x:0,y:1}:{x:0,y:-1}
  const end={x:p.center.x+v.x*.38,y:p.center.y+v.y*.38},net=netOf(p)
  if(net){trace(p.schematic_sheet_id,[p.center,end],net.subcircuit_connectivity_map_key);label(p.schematic_sheet_id,p,end,v.x<0?'right':v.x>0?'left':v.y>0?'bottom':'top')}
  else text(p.schematic_sheet_id,'NC',end.x,end.y,.14,v.x<0?'right':'left',p.schematic_component_id)
 }
 if(placed.size!==byName.size)throw new Error('Missing functional schematic parts: '+[...byName.keys()].filter(n=>!placed.has(n)).join(', '))
 if(newPorts.size!==json.filter(e=>e.type==='schematic_port').length)throw new Error('Schematic physical pin coverage changed')
 return out
}
