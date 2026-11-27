"""Verify the rendered TSX netlist for the NEMA14 JST engineering study."""
import json
import sys
from native_sources import source_owner_names

with open(sys.argv[1]) as board_file:
    elements = json.load(board_file)

def of_type(name):
    return (e for e in elements if e["type"] == name)

parts = {e["source_component_id"]: e["name"] for e in of_type("source_component")}
owners = source_owner_names(elements)
ports = {
    e["source_port_id"]: (owners[e["source_component_id"]], e["name"])
    for e in of_type("source_port")
}
nets = {e["source_net_id"]: e["name"] for e in of_type("source_net")}
port_nets = {}
for trace in of_type("source_trace"):
    for source_port in trace["connected_source_port_ids"]:
        for source_net in trace["connected_source_net_ids"]:
            port_nets.setdefault(ports[source_port], set()).add(nets[source_net])

def expect(part, port, net):
    assert port_nets.get((part, port)) == {net}, (part, port, port_nets.get((part, port)))

for channel, driver_output, adc_pin in (("A", "OUT1A", "GPIO26"), ("B", "OUT2A", "GPIO27")):
    driver_net = f"{channel}_DRV_PLUS"
    winding_net = f"{channel}_PLUS"
    raw_net = f"I_{channel}_RAW"
    adc_net = f"I_{channel}_ADC"
    for row in [
        ("U_DRV", driver_output, driver_net),
        (f"R_SHUNT_{channel}", "pin1", driver_net),
        (f"R_SHUNT_{channel}", "pin2", winding_net),
        (f"U_I{channel}", "IN_POS", driver_net),
        (f"U_I{channel}", "IN_NEG", winding_net),
        (f"U_I{channel}", "VS", "V3V3"),
        (f"U_I{channel}", "REF1", "V3V3"),
        (f"U_I{channel}", "REF2", "GND"),
        (f"U_I{channel}", "OUT", raw_net),
        (f"R_I{channel}", "pin1", raw_net),
        (f"R_I{channel}", "pin2", adc_net),
        (f"C_IADC_{channel}", "pin1", adc_net),
        ("U_MCU", adc_pin, adc_net),
        ("J_MOTOR", winding_net, winding_net),
        ("J_MOTOR", f"{channel}_MINUS", f"{channel}_MINUS"),
    ]:
        expect(*row)

expect("U_MCU", "GPIO4", "TEMP_SDA")
expect("U_MCU", "GPIO5", "TEMP_SCL")
expect("U_DRV", "SENSE1", "SENSE1")
expect("U_DRV", "SENSE2", "SENSE2")
by_name = {parts[e["source_component_id"]]: e for e in of_type("pcb_component") if e["source_component_id"] in parts}
for name, layer in (("C_ENCODER", "top"), ("C_ENCODER_BULK", "top"), ("U_ENCODER", "bottom")):
    assert by_name[name]["layer"] == layer and by_name[name]["do_not_place"], name

motor = next(e for e in of_type("source_component") if e["name"] == "J_MOTOR")
assert motor["manufacturer_part_number"] == "SM04B-SRSS-TB(LF)(SN)"
assert motor["supplier_part_numbers"]["jlcpcb"] == ["C160404"]

print("Both independent winding channels, RP2040 I²C/ADC pins, DNP population policy and side-entry connector verified.")

# Physical PW/TSSOP pin numbers from TI INA240 Rev C, section 6.
# SOIC has a different pinout and must not be accepted as a drop-in replacement.
physical_pins = {1:'NC',2:'IN_POS',3:'IN_NEG',4:'GND',5:'VS',6:'REF2',7:'REF1',8:'OUT'}
source_by_name={e['name']:e for e in of_type('source_component')}
for phase in 'AB':
    amp=source_by_name['U_I'+phase]
    assert amp['manufacturer_part_number']=='INA240A1PWR'
    actual={e['pin_number']:e['name'] for e in of_type('source_port') if e['source_component_id']==amp['source_component_id']}
    assert actual==physical_pins,actual
    nc=next(e for e in of_type('source_port') if e['source_component_id']==amp['source_component_id'] and e['pin_number']==1)
    assert nc.get('do_not_connect') and not port_nets.get(('U_I'+phase,'NC'))
    assert abs(source_by_name['R_SHUNT_'+phase]['resistance']-.05)<1e-9
    assert abs(source_by_name['R_I'+phase]['resistance']-100)<1e-9
    assert abs(source_by_name['C_IADC_'+phase]['capacitance']-10e-9)<1e-15
    for name,net in [('C_I'+phase,'V3V3'),('C_IADC_'+phase,'I_'+phase+'_ADC')]:
        expect(name,'pin1',net);expect(name,'pin2','GND')
assert by_name['J_MOTOR']['insertion_direction']=='from_right'
assert all(abs(by_name['U_ENCODER']['center'][a])<1e-6 for a in ['x','y'])
for name,pin,net in [('J_MOTOR',1,'A_PLUS'),('J_MOTOR',2,'A_MINUS'),('J_MOTOR',3,'B_PLUS'),('J_MOTOR',4,'B_MINUS')]:
    terminal=next(e for e in of_type('source_port') if e['source_component_id']==source_by_name[name]['source_component_id'] and e['pin_number']==pin)
    assert terminal['name']==net
print('Physical INA240 PW pinout, 50 mΩ values, output filters, header direction/order and encoder axis verified.')

# Dedicated source branches preserve the intended pad pickup; routed copper must
# still be checked for sharing a high-current segment away from the shunt pad.
for phase in 'AB':
    expected=[('POWER_'+phase+'_DRV',('U_DRV','OUT1A' if phase=='A' else 'OUT2A'),('R_SHUNT_'+phase,'pin1'),.45),('POWER_'+phase+'_COIL',('R_SHUNT_'+phase,'pin2'),('J_MOTOR',phase+'_PLUS'),.45),('KELVIN_'+phase+'_POS',('R_SHUNT_'+phase,'pin1'),('U_I'+phase,'IN_POS'),.16),('KELVIN_'+phase+'_NEG',('R_SHUNT_'+phase,'pin2'),('U_I'+phase,'IN_NEG'),.16)]
    for name,a,b,width in expected:
        t=next(e for e in of_type('source_trace') if e.get('name')==name)
        assert {ports[k] for k in t['connected_source_port_ids']}=={a,b},name
        assert abs(t['min_trace_thickness']-width)<1e-9,name
print('NEMA14 JST dedicated power and Kelvin source branches verified; physical copper pickup remains unverified.')
