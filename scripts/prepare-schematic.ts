/** Produce readable A4 sheets from the source electrical graph. PCB/CAD records are untouched.
 * Named net stubs connect across pages; NC pins are explicitly marked.
 */
export function prepareSchematic(json: any[]) {
  const template=json.find(e=>e.type==='schematic_sheet')
  if (!template) throw new Error('An explicit A4 schematic sheet is required')
  const source=new Map(json.filter(e=>e.type==='source_component').map(e=>[e.source_component_id,e]))
  const sourcePorts=new Map(json.filter(e=>e.type==='source_port').map(e=>[e.source_port_id,e]))
  const nets=new Map(json.filter(e=>e.type==='source_net').map(e=>[e.subcircuit_connectivity_map_key,e]))
  const components=json.filter(e=>e.type==='schematic_component')
  template.name=template.name.replace(/_\d+$/, '')
  const notes=[...new Map(json.filter(e=>e.type==='schematic_text'&&!e.schematic_component_id&&!e.source_trace_id&&!e.schematic_text_id.startsWith('a4_text_')).map(e=>[e.text+JSON.stringify(e.position),e])).values()]
  // Preserve direct pin-to-pin networks, including the WCH debug signals and boot jumper.
  const groups=new Map<string,any[]>()
  for(const p of sourcePorts.values()) if(p.subcircuit_connectivity_map_key) {
   const key=p.subcircuit_connectivity_map_key;groups.set(key,[...(groups.get(key)??[]),p])
  }
  for(const [key,ports] of groups) if(!nets.has(key)&&ports.length>1) {
   const name=ports.find(p=>!/^pin\d/.test(p.name))?.name??ports[0].name
   nets.set(key,{name,subcircuit_connectivity_map_key:key})
  }
  const widths:Record<string,number>={U_MCU:source.get(components.find(c=>source.get(c.source_component_id)?.name==='U_MCU')?.source_component_id)?.manufacturer_part_number==='RP2040'?2.70:3.27,U_DRV:2.51,J_PD:2.055,J_DATA:2.055,U_PD:1.94,U_FLASH:1.75,J_BOOT:1.2,Y_MCU:1.96,U_BUCK:1.75,U_LDO:1.84,J_MOTOR:2.51,J_DEBUG:2.12,U_ESD:1.84,U_VM_ISO:1.865}

  const pages:any[][]=[]
  // Large ICs have dedicated sheets; the remaining symbols use generous two-column cells.
  for(const c of components.filter(c=>['U_MCU','U_DRV'].includes(source.get(c.source_component_id)?.name))) pages.push([c])
  const rest=components.filter(c=>!['U_MCU','U_DRV'].includes(source.get(c.source_component_id)?.name))
  for(let i=0;i<rest.length;i+=6) pages.push(rest.slice(i,i+6))
  const out=json.filter(e=>!e.type.startsWith('schematic_'))
  let sequence=0
  const text=(sheet:string,value:string,x:number,y:number,anchor='left',size=.20,component?:string)=>out.push({type:'schematic_text',schematic_text_id:`a4_text_${sequence++}`,schematic_sheet_id:sheet,text:value,position:{x,y},anchor,rotation:0,font_size:size,color:'#006464',...(component?{schematic_component_id:component}:{})})
  pages.forEach((page,index)=>{
    const sheet=`schematic_sheet_${index}`
    const names=page.map(c=>source.get(c.source_component_id).name)
    out.push({...template,schematic_sheet_id:sheet,name:`${template.name}_${index+1}`,display_name:`${template.name} ${index+1}/${pages.length}`,sheet_index:index,sheet_size:'a4',sheet_width:297,sheet_height:210,center:{x:0,y:0}})
    for(const n of notes)out.push({...n,schematic_text_id:`a4_note_${sequence++}`,schematic_sheet_id:sheet})
    text(sheet,`SHEET ${index+1}/${pages.length} - ${names.join(', ')}`,-15,9.75,'left',.22)
    text(sheet,'Named nets connect across all pages. NC = intentionally unconnected pin.',-15,-8.75,'left',.19)
    const positions=new Map<string,{x:number;y:number}>()
    page.forEach((c,i)=>positions.set(source.get(c.source_component_id).name,page.length===1?{x:-4.4,y:.1}:{x:i%2===0?-9.3:1,y:6.6-Math.floor(i/2)*5.2}))
    const caps=new Map<string,any[]>()
    for(const c of page) if(source.get(c.source_component_id).ftype==='simple_capacitor') {
     const pins=[...sourcePorts.values()].filter(p=>p.source_component_id===c.source_component_id)
     const key=pins.map(p=>p.subcircuit_connectivity_map_key).sort().join('|')
     caps.set(key,[...(caps.get(key)??[]),c])
    }
    for(const group of caps.values()) if(group.length>1) {
     const start=positions.get(source.get(group[0].source_component_id).name)!
     const x=Math.min(start.x,5.5-(group.length-1)*1.6)
     group.forEach((c,i)=>positions.set(source.get(c.source_component_id).name,{x:x+i*1.6,y:start.y}))
    }
    if(positions.has('R_DM')&&positions.has('R_DP')){
     const p=positions.get('R_DM')!;positions.set('R_DP',{x:p.x,y:p.y+2.1})
    }
    page.forEach((old,cell)=>{
      const s=source.get(old.source_component_id)
      const single=page.length===1
      const center=positions.get(s.name)!
      const ports=json.filter(e=>e.type==='schematic_port'&&e.schematic_component_id===old.schematic_component_id).sort((a,b)=>a.pin_number-b.pin_number)
      const boxed=!old.symbol_name
      const half=Math.ceil(ports.length/2),spacing=.44
      const vertical=s.name==='J_BOOT'||s.name==='R_PD'||s.name==='D_TVS'
      const size=boxed?{width:widths[s.name]??2.4,height:['J_BOOT','D_TVS'].includes(s.name)?1.8:Math.max(1.2,half*spacing+.4)}:vertical?{width:old.size.height,height:old.size.width}:old.size
      const c={...old,center,size,schematic_sheet_id:sheet,pin_spacing:spacing,...(boxed?{is_box_with_pins:true}:{})}
      delete c.schematic_group_id
      if(s.name==='R_PD') c.symbol_name='boxresistor_down'
      out.push(c)
      text(sheet,s.name,center.x-size.width/2,center.y+size.height/2+.50,'left',.24,c.schematic_component_id)
      const value=s.display_resistance??s.display_capacitance??s.display_inductance??s.manufacturer_part_number??'PCB solder interface'
      text(sheet,value,center.x-size.width/2,center.y-size.height/2-.48,'left',.19,c.schematic_component_id)
      ports.forEach((oldPort,i)=>{
        const left=i<half,sign=left?-1:1,row=left?i:i-half
        const verticalSign=(i===0?1:-1)*(s.name==='D_TVS'?-1:1)
        const pinCenter=vertical?{x:center.x,y:center.y+verticalSign*(size.height/2+(boxed?.35:0))}:boxed?{x:center.x+sign*(size.width/2+.35),y:center.y+(half-1)*spacing/2-row*spacing}:{x:center.x+oldPort.center.x-old.center.x,y:center.y+oldPort.center.y-old.center.y}
        const direction=vertical?(verticalSign>0?'up':'down'):boxed?(left?'left':'right'):oldPort.facing_direction
        const port={...oldPort,center:pinCenter,schematic_sheet_id:sheet,display_pin_label_font_size:.17,...(boxed||vertical?{side_of_component:direction==='up'?'top':direction==='down'?'bottom':direction,facing_direction:direction,distance_from_component_edge:.35}:{})}
        out.push(port)
        const sp=sourcePorts.get(oldPort.source_port_id),net=nets.get(sp?.subcircuit_connectivity_map_key)
        const vec=direction==='left'?{x:-1,y:0}:direction==='right'?{x:1,y:0}:direction==='up'?{x:0,y:1}:{x:0,y:-1}
        const end={x:pinCenter.x+vec.x*.5,y:pinCenter.y+vec.y*.5}
        if(net){
          out.push({type:'schematic_trace',schematic_trace_id:`a4_trace_${sequence++}`,source_trace_id:json.find(e=>e.type==='source_trace'&&e.connected_source_port_ids?.includes(sp.source_port_id))?.source_trace_id,edges:[{from:pinCenter,to:end}],junctions:[],schematic_sheet_id:sheet,subcircuit_connectivity_map_key:net.subcircuit_connectivity_map_key})
          // Use native net-label records for electrical connectivity and horizontal readable text.
          const side=vec.x<0?'right':vec.x>0?'left':vec.y>0?'bottom':'top'
          out.push({type:'schematic_net_label',schematic_net_label_id:`a4_net_${sequence++}`,source_net_id:net.source_net_id,text:net.name,anchor_position:end,center:end,anchor_side:side,schematic_sheet_id:sheet})
        }else text(sheet,'NC',end.x,end.y,vec.x<0?'right':'left',.17,c.schematic_component_id)
      })
    })
  })
  if(out.filter(e=>e.type==='schematic_component').length!==components.length)throw new Error('Schematic component coverage changed')
  return out
}
