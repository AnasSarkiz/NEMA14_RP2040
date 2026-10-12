/** Supplier imports use chip JSX; classify passive connectors/crystal accurately for ERC. */
export function classifySource(json:any[]) {
 for(const c of json.filter(e=>e.type==='source_component')) {
  if(c.name.startsWith('J_')) c.ftype='simple_connector'
  if(c.name==='D_STATUS') c.ftype='simple_led'
  if(c.name.startsWith('Q_STATUS_')) Object.assign(c,{ftype:'simple_transistor',transistor_type:'npn'})
  if(c.name==='Q_BUZZER') Object.assign(c,{ftype:'simple_mosfet',channel_type:'n',mosfet_mode:'enhancement'})
  if(c.name==='BZ1') c.ftype='simple_buzzer'
  if(c.name==='D_TVS') c.ftype='simple_diode'
  if(c.name==='Y_MCU') Object.assign(c,{ftype:'simple_crystal',frequency:12_000_000,load_capacitance:10})
 }
 return json
}
