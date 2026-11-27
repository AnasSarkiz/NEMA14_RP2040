/** NEMA14 JST mating envelope, from the JST SH catalog assembly/housing drawings.
 * This is a conservative envelope, not a supplier model of contacts or a latch.
 */
export type Box = { min: [number, number, number]; max: [number, number, number] }
export function getSideEntryPlug(board: any[]) {
 const source = board.find(e => e.type === 'source_component' && e.name === 'J_MOTOR')
 if (source?.manufacturer_part_number !== 'SM04B-SRSS-TB(LF)(SN)') throw Error('NEMA14 JST requires the side-entry header')
 const pcb = board.find(e => e.type === 'pcb_component' && e.source_component_id === source.source_component_id)
 const cad = board.find(e => e.type === 'cad_component' && e.source_component_id === source.source_component_id)
 if (pcb?.insertion_direction !== 'from_right' || Math.abs(cad?.rotation.z - 90) > 1e-6) throw Error('NEMA14 JST plug model requires the checked right-side mating axis')
 const pins = board.filter(e => e.type === 'source_port' && e.source_component_id === source.source_component_id && e.pin_number >= 1 && e.pin_number <= 4).sort((a,b) => a.pin_number-b.pin_number)
 if (pins.map(e => e.name).join(',') !== 'A_PLUS,A_MINUS,B_PLUS,B_MINUS') throw Error('NEMA14 JST winding pin order changed')
 const surface = board.find(e => e.type === 'pcb_board').thickness / 2
 if (pcb.layer !== 'top' || Math.abs(cad.position.z-surface)>1e-6 || Math.abs(cad.rotation.x)+Math.abs(cad.rotation.y)>1e-6) throw Error('NEMA14 JST plug model requires the top-side header datum')
 const origin = cad.model_origin_position
 const angle = cad.rotation.z * Math.PI/180, c=Math.cos(angle),s=Math.sin(angle)
 const xy=(x:number,y:number)=>[cad.position.x+c*(x-origin.x)-s*(y-origin.y),cad.position.y+s*(x-origin.x)+c*(y-origin.y)]
 const box=(xmin:number,xmax:number,ymin:number,ymax:number,zmin:number,zmax:number):Box=>{
  const points=[[xmin,ymin],[xmin,ymax],[xmax,ymin],[xmax,ymax]].map(([x,y])=>xy(x,y))
  return {min:[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),zmin],max:[Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1])),zmax]}
 }
 // Body rear datum +2.125 follows the 4.25 mm header body drawing.
 // The 6.25 mm assembly depth puts the wire end at local Y=-4.125.
 const housing=box(-1,4,-4.125,.875,surface+.15,surface+2.95)
 const tolerance=.15
 const seated:Box={min:[housing.min[0]-tolerance,housing.min[1]-tolerance,surface],max:housing.max.map(v=>v+tolerance) as [number,number,number]}
 const withdrawal=5 // Engineering screen: one complete housing length, not a force/stroke rating.
 const sweep:Box={min:[...seated.min],max:[seated.max[0]+withdrawal,seated.max[1],seated.max[2]]}
 const edge=board.find(e=>e.type==='pcb_board').width/2
 const grip:Box={min:[Math.max(edge,housing.min[0]),housing.min[1]-2,surface],max:[housing.max[0]+2,housing.max[1]+2,housing.max[2]+2]}
 return {
  header_mpn:source.manufacturer_part_number,housing_mpn:'SHR-04V-S',insertion_direction:pcb.insertion_direction,
  nominal_housing_dimensions_mm:[5,5,2.8],catalog_mated_depth_mm:6.25,catalog_mated_height_mm:2.95,
  housing,seated_envelope:seated,withdrawal_sweep:sweep,service_grip_envelope:grip,
  exposed_housing_length_mm:Math.max(0,housing.max[0]-edge),withdrawal_screen_mm:withdrawal,
  geometric_tolerance_mm:tolerance,service_lateral_and_vertical_allowance_mm:2,
  supplier_model:false,actual_cable_handling_verified:false,
  source:'https://www.jst-mfg.com/product/pdf/eng/eSH.pdf',
  assumptions:['SHR-04V-S without protrusions, not the 7 mm wide -B housing','Rear body datum +2.125 mm from the 4.25 mm body drawing','5 mm straight withdrawal and 2 mm service allowance are engineering screens','Exposed housing length is reported; grip force, wire bends, custom cable and operator access require physical verification']
 }
}
