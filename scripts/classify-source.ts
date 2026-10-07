/** Supplier imports use chip JSX; classify passive connectors/crystal accurately for ERC. */
export function classifySource(json:any[]) {
 for(const c of json.filter(e=>e.type==='source_component')) {
  if(c.name.startsWith('J_')) c.ftype='simple_connector'
  if(c.name==='D_TVS') c.ftype='simple_diode'
  if(c.name==='Y_MCU') Object.assign(c,{ftype:'simple_crystal',frequency:12_000_000,load_capacitance:10})
 }
 return json
}
