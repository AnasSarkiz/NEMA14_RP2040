"""Generate assembly/BOM and hashes from the final delivered copper, not an old board."""
import csv,hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
j=json.loads((root/'artifacts/board.circuit.json').read_text());parts=[e for e in j if e['type']=='source_component'];pcb={e['source_component_id']:e for e in j if e['type']=='pcb_component'}
with (root/'artifacts/bom.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','MPN','Value','Voltage rating (V)','Tolerance','PCB X mm','PCB Y mm','Rotation deg','Assembly side','Review note'])
 for e in parts:
  p=pcb[e['source_component_id']];n=e['name'];note=''
  if n in ['R_SA','R_SB']:note='0.25 ohm, 1%, >=0.25 W; verify Kelvin current-sense layout'
  if n in ['C_BUCK_OUT1','C_BUCK_OUT2']:note='X5R/X7R, check effective capacitance at 3.3 V'
  if n=='C_BUCK_IN':note='X7R, check effective capacitance at 15 V'
  if n=='L_BUCK':note='Verify exact land pattern, saturation and RMS ripple rating'
  if n=='Y_MCU':note='12 MHz, 10 pF CL, validate startup/drive level'
  if n.startswith('J_'):note='Motor/debug/boot use solder pads; USB receptacles require assembly'
  val=e.get('display_resistance',e.get('display_capacitance',e.get('display_inductance','')))
  w.writerow([n,e.get('manufacturer_part_number',''),val,e.get('max_voltage_rating',''),e.get('tolerance',''),p['center']['x'],p['center']['y'],p.get('rotation',0),p.get('layer','top'),note])
files=['artifacts/board.circuit.json','artifacts/unrouted.circuit.json','artifacts/freerouting-input.dsn','artifacts/board.ses','artifacts/nema14-gerbers.zip']
hashes={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files if (root/f).exists()}
r={'project':'NEMA14_RP2040','motor':'14HM11-0404S','assemblySide':'top','copperLayers':2,'boardSizeMm':[35,35],'mountHolePitchMm':[26,26],'mountHoleDiameterMm':3.2,'rearFitVerified':False,'usbMouthEdgeXmm':[-17.5,17.5],'componentCount':len(parts),'firmwareImplemented':False,'manufacturingRelease':False,'sha256':hashes}
(root/'artifacts/verification.json').write_text(json.dumps(r,indent=2)+'\n')
print('Generated BOM and verification hashes for',len(parts),'components')
