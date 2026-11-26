"""Regression: source names do not bridge layers or prove physical clearance."""
from pathlib import Path
from routing_geometry import layer_copper,shared_outside_pad,pad_cut_topology,resolve_copper_nets
from shapely.geometry import box
import importlib.util,json,tempfile,unittest
spec=importlib.util.spec_from_file_location('copper',Path(__file__).with_name('inspect-copper.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
 b=[{'type':'pcb_board','width':35,'height':35,'min_board_edge_clearance':.25,'min_trace_to_pad_edge_clearance':.15}]
 b+=[{'type':'source_net','subcircuit_connectivity_map_key':'N','name':'GND'},{'type':'source_component','source_component_id':'C','name':'TEST'}]
 for i,(x,layer) in enumerate([(0,'top'),(4,'bottom')]):
  b += [{'type':'source_port','source_port_id':str(i),'source_component_id':'C','name':'P'+str(i),'subcircuit_connectivity_map_key':'N'},{'type':'pcb_port','pcb_port_id':str(i),'source_port_id':str(i)},{'type':'pcb_smtpad','pcb_smtpad_id':str(i),'pcb_port_id':str(i),'shape':'rect','x':x,'y':0,'width':1,'height':1,'layer':layer}]
 for i,(a,z,l) in enumerate([(0,2,'top'),(2,4,'bottom')]):b.append({'type':'pcb_trace','pcb_trace_id':'T'+str(i),'subcircuit_connectivity_map_key':'N','route':[{'route_type':'wire','x':a,'y':0,'width':.16,'layer':l},{'route_type':'wire','x':z,'y':0,'width':.16,'layer':l}]})
 return b
class GeometryRegression(unittest.TestCase):
 def run_board(self,b):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'board.json';p.write_text(json.dumps(b));return m.inspect(p)
 def test_names_and_crossing_coordinates_do_not_bridge_layers(self):
  r=self.run_board(fixture());self.assertTrue(r['geometric_clearance_pass']);self.assertFalse(r['full_board_connectivity_pass']);self.assertEqual(len(r['disconnected_nets']),1)
 def test_real_through_via_can_bridge_layers(self):
  b=fixture();b.append({'type':'pcb_via','pcb_via_id':'V','x':2,'y':0,'outer_diameter':.45,'hole_diameter':.3,'layers':['top','inner1','inner2','bottom'],'subcircuit_connectivity_map_key':'N'});self.assertTrue(self.run_board(b)['full_board_connectivity_pass'])
 def test_via_on_wrong_layers_does_not_bridge(self):
  b=fixture();b.append({'type':'pcb_via','pcb_via_id':'V','x':2,'y':0,'outer_diameter':.45,'hole_diameter':.3,'layers':['inner1','inner2'],'subcircuit_connectivity_map_key':'N'});self.assertFalse(self.run_board(b)['full_board_connectivity_pass'])
 def test_independent_screen_rejects_via_pad_gap_below_rule(self):
  b=fixture();b=[e for e in b if e['type']!='pcb_trace'];next(e for e in b if e.get('pcb_smtpad_id')=='0')['width']=2;b.append({'type':'source_net','subcircuit_connectivity_map_key':'OTHER','name':'CP2'});b.append({'type':'pcb_via','pcb_via_id':'V','x':1.331,'y':0,'outer_diameter':.45,'hole_diameter':.3,'layers':['top','inner1','inner2','bottom'],'subcircuit_connectivity_map_key':'OTHER'});r=self.run_board(b);self.assertFalse(r['geometric_clearance_pass']);self.assertEqual(len(r['clearance_violations']),1);self.assertAlmostEqual(r['clearance_violations'][0]['clearance_mm'],.106,places=5)
class NativeAuthoredIdentityRegression(unittest.TestCase):
 def test_native_authored_trace_resolves_through_source_id_without_mutating_input(self):
  b=[{'type':'source_trace','source_trace_id':'S','subcircuit_connectivity_map_key':'N'},{'type':'pcb_trace','pcb_trace_id':'T','source_trace_id':'S','route':[]},{'type':'pcb_via','pcb_via_id':'V','pcb_trace_id':'T'}]
  out=resolve_copper_nets(b);self.assertEqual(out[1]['subcircuit_connectivity_map_key'],'N');self.assertEqual(out[2]['subcircuit_connectivity_map_key'],'N');self.assertNotIn('subcircuit_connectivity_map_key',b[1]);self.assertEqual(out[1]['route'],b[1]['route'])
 def test_conflicting_explicit_source_identity_fails_closed(self):
  b=[{'type':'source_trace','source_trace_id':'S','subcircuit_connectivity_map_key':'N'},{'type':'pcb_trace','pcb_trace_id':'T','source_trace_id':'S','subcircuit_connectivity_map_key':'OTHER','route':[]}]
  with self.assertRaises(ValueError):resolve_copper_nets(b)
 def test_unresolved_identity_is_not_guessed_from_crossing_geometry(self):
  b=[{'type':'pcb_trace','pcb_trace_id':'T','source_trace_id':'MISSING','route':[]}];self.assertNotIn('subcircuit_connectivity_map_key',resolve_copper_nets(b)[0])

class KelvinRegression(unittest.TestCase):
 def wire(self,a,z,width=.16,layer='top'):
  return {'type':'pcb_trace','subcircuit_connectivity_map_key':'N','route':[{'route_type':'wire','x':a[0],'y':a[1],'width':width,'layer':layer},{'route_type':'wire','x':z[0],'y':z[1],'width':width,'layer':layer}]}
 def test_separate_pickups_can_share_only_the_actual_pad(self):
  k=layer_copper([self.wire((0,0),(0,3))],[],m.pad_shape);p=layer_copper([self.wire((0,0),(3,0),.45)],[],m.pad_shape);self.assertAlmostEqual(shared_outside_pad(k,p,box(-.6,-.6,.6,.6),'top'),0)
 def test_shared_winding_stub_outside_pad_is_rejected(self):
  k=layer_copper([self.wire((0,0),(3,0))],[],m.pad_shape);p=layer_copper([self.wire((0,0),(3,0),.45)],[],m.pad_shape);self.assertGreater(shared_outside_pad(k,p,box(-.6,-.6,.6,.6),'top'),.1)
 def test_common_barrel_is_not_masked_by_top_pad_projection(self):
  via={'type':'pcb_via','x':0,'y':0,'hole_diameter':.3,'outer_diameter':.45,'layers':['top','inner1','inner2','bottom'],'subcircuit_connectivity_map_key':'N'}
  def route(a,z):return {'type':'pcb_trace','subcircuit_connectivity_map_key':'N','route':[{'route_type':'via','x':0,'y':0,'from_layer':a,'to_layer':z}]}
  k=layer_copper([route('top','inner1')],[via],m.pad_shape);p=layer_copper([route('inner2','bottom')],[via],m.pad_shape);self.assertGreater(shared_outside_pad(k,p,box(-1,-1,1,1),'top'),.1)
class PadCutRegression(unittest.TestCase):
 def base(self):
  b=[{'type':'source_component','source_component_id':'C','name':'TEST'}]
  for pid,x,y,layer in [('S',0,0,'top'),('A',0,3,'top'),('P',3,0,'top')]:b += [{'type':'source_port','source_port_id':pid,'source_component_id':'C','name':pid,'subcircuit_connectivity_map_key':'N'},{'type':'pcb_port','pcb_port_id':pid,'source_port_id':pid},{'type':'pcb_smtpad','pcb_smtpad_id':pid,'pcb_port_id':pid,'shape':'rect','x':x,'y':y,'width':1.2,'height':1.2,'layer':layer}]
  return b
 def wire(self,a,z,layer='top'):return {'type':'pcb_trace','subcircuit_connectivity_map_key':'N','route':[{'route_type':'wire','x':a[0],'y':a[1],'width':.16,'layer':layer},{'route_type':'wire','x':z[0],'y':z[1],'width':.16,'layer':layer}]}
 def check(self,b):return pad_cut_topology(b,'N','S','A','P',box(-.6,-.6,.6,.6),'top',m.pad_shape)
 def test_actual_pad_star_passes_without_trace_names(self):
  b=self.base()+[self.wire((0,0),(3,0)),self.wire((0,0),(0,3))];self.assertTrue(self.check(b)['actual_shunt_pad_is_required_pickup'])
 def test_shared_power_stub_before_pickup_fails(self):
  b=self.base()+[self.wire((0,0),(3,0)),self.wire((1,0),(1,3)),self.wire((1,3),(0,3))];self.assertFalse(self.check(b)['actual_shunt_pad_is_required_pickup'])
 def test_common_barrel_beneath_pad_fails(self):
  b=self.base()
  for e in b:
   if e['type']=='pcb_smtpad' and e['pcb_port_id'] in ['A','P']:e['layer']='inner1' if e['pcb_port_id']=='A' else 'bottom'
  b += [self.wire((0,0),(0,3),'inner1'),self.wire((0,0),(3,0),'bottom'),{'type':'pcb_via','x':0,'y':0,'outer_diameter':.45,'hole_diameter':.3,'layers':['top','inner1','inner2','bottom'],'subcircuit_connectivity_map_key':'N'}];self.assertFalse(self.check(b)['actual_shunt_pad_is_required_pickup'])
 def test_cut_splits_one_wire_into_independent_pieces(self):
  b=self.base()
  next(e for e in b if e['type']=='pcb_smtpad' and e['pcb_port_id']=='A').update(x=-3,y=0)
  b += [self.wire((-3,0),(3,0))];self.assertTrue(self.check(b)['actual_shunt_pad_is_required_pickup'])
if __name__=='__main__':unittest.main()
